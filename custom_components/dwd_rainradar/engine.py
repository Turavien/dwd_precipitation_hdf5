"""Engine for DWD data processing."""

from __future__ import annotations

import asyncio

from datetime import timedelta

from homeassistant.core import HomeAssistant

from .backfill import Backfill
from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .products import (
    RS,
    RV,
    RW,
)
from .state import State
from .storage import Storage


class Engine:
    """Coordinate download, storage and parsing."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the engine."""

        self._storage = Storage(
            hass,
        )

        self._decoder = Decoder()

        self._history = History(
            self._storage,
            self._decoder,
        )

        self._fetcher = Fetcher(
            hass,
        )

        self._backfill = Backfill(
            self._fetcher,
            self._history,
            self._decoder,
        )

        self._state = State()

        self._products = (
            RS,
            RV,
            RW,
        )

        self._update_task: asyncio.Task[State] | None = None

        self._backfill_completed: set[str] = set()

        self._backfill_tasks: set[
            asyncio.Task[None]
        ] = set()

    async def async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Update all configured DWD products."""

        if self._update_task is not None:

            return await self._update_task

        self._update_task = asyncio.create_task(
            self._async_update(
                grid_cell,
            )
        )

        try:

            return await self._update_task

        finally:

            self._update_task = None

    async def _async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Execute one complete update."""

        decoded_products = {}

        updated = False

        for product in self._products:

            metadata = await self._storage.async_read_metadata(
                product.key,
            )

            result = await self._fetcher.async_download(
                product,
                metadata,
            )

            if not result.downloaded:

                try:

                    result = await self._history.product(
                        product,
                    ).read_latest()

                except FileNotFoundError:

                    result = await self._fetcher.async_download(
                        product,
                    )

            decoded = self._decoder.decode(
                result,
                grid_cell,
            )

            latest = decoded.values[-1]

            if result.downloaded:

                await self._history.product(
                    product,
                ).store(
                    result,
                )

                if (
                    product.key
                    not in self._backfill_completed
                ):

                    self._backfill_completed.add(
                        product.key,
                    )

                    self._start_backfill(
                        product,
                        latest.valid_until
                        - product.retention
                        + product.interval / 2,
                    )

                updated = True

            decoded_products[
                product.key
            ] = decoded

        if updated:
            await self._history.prune()

        rw = decoded_products.get(
            "rw",
        )

        rolling: dict[str, float | None] = {}

        if (
            rw is not None
            and rw.values
        ):

            rolling = await self._history.rolling_summaries(
                rw_anchor=rw.values[-1].valid_until,
                grid_cell=grid_cell,
            )

        self._state.update(
            decoded_products,
            rolling,
        )

        return self._state

    def _start_backfill(
        self,
        product,
        since,
    ) -> None:
        """Start one backfill task."""

        task = asyncio.create_task(
            self._backfill.async_backfill(
                product,
                since,
            )
        )

        self._backfill_tasks.add(
            task,
        )

        task.add_done_callback(
            self._backfill_tasks.discard,
        )


"""Engine for DWD data processing."""

from __future__ import annotations

import asyncio

from datetime import (
    datetime,
    timedelta,
)

from homeassistant.core import HomeAssistant
from .backfill import Backfill
from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .models import (
    DecodedProduct,
)
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

        self._forecast_products = (
            RS,
            RV,
        )

        self._update_lock = asyncio.Lock()

        self._backfill_completed: set[str] = set()

        self._backfill_tasks: set[
            asyncio.Task[None]
        ] = set()

    async def async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Update all configured DWD products."""

        async with self._update_lock:

            return await self._async_update(
                grid_cell,
            )

    async def _async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Execute one complete update."""

        state = State()

        decoded_products: dict[str, DecodedProduct] = {}

        for product in self._forecast_products:

            metadata = await self._storage.async_read_metadata(
                product.key,
            )

            result = await self._fetcher.async_download(
                product,
                metadata,
            )

            if not result.downloaded:

                try:

                    result = await self._storage.async_read_latest_product(
                        product,
                    )

                except FileNotFoundError:

                    result = await self._fetcher.async_download(
                        product,
                    )

            decoded_products[
                product.key
            ] = self._decoder.decode(
                result,
                grid_cell,
            )

            if result.downloaded:

                await self._storage.async_store_product(
                    result,
                )

                await self._storage.async_delete_old_files(
                    product,
                    result.valid_until,
                )

        product = RW

        metadata = await self._storage.async_read_metadata(
            product.key,
        )

        result = await self._fetcher.async_download(
            product,
            metadata,
        )

        if not result.downloaded:

            try:

                result = await self._history.read_latest()

            except FileNotFoundError:

                result = await self._fetcher.async_download(
                    product,
                )

        decoded = self._decoder.decode(
            result,
            grid_cell,
        )

        decoded_products[
            product.key
        ] = decoded

        latest = decoded.values[-1]

        if result.downloaded:

            await self._history.store(
                result,
            )

            await self._history.prune()

            if (
                RW.key
                not in self._backfill_completed
            ):

                since = (
                    latest.valid_until
                    - RW.retention
                    + RW.interval / 2
                )

                self._backfill_completed.add(
                    RW.key,
                )

                self._start_backfill(
                    since,
                )

        rw = decoded_products.get(
            "rw",
        )

        rolling: dict[str, float | None] = {}

        if (
            rw is not None
            and rw.values
        ):

            rolling = await self._history.rolling_summaries(
                latest_rw=rw,
                grid_cell=grid_cell,
            )

        state.update(
            decoded_products,
            rolling,
        )

        return state

    def _start_backfill(
        self,
        since: datetime,
    ) -> None:
        """Start one RW backfill task."""

        task = asyncio.create_task(
            self._backfill.async_backfill(
                since,
            )
        )

        self._backfill_tasks.add(
            task,
        )

        task.add_done_callback(
            self._backfill_tasks.discard,
        )

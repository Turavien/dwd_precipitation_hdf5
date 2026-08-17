"""Engine for DWD data processing."""

from __future__ import annotations

import asyncio

from collections.abc import Callable

from datetime import datetime

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

        self._hass = hass

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

        self._grid_cell_references: dict[
            tuple[int, int],
            int,
        ] = {}

        self._rolling_cache_anchor: datetime | None = None

        self._rolling_cache_grid_cells: tuple[
            tuple[int, int],
            ...
        ] = ()

        self._rolling_cache: dict[
            tuple[int, int],
            dict[str, float | None],
        ] = {}

        self._update_callbacks: set[
            Callable[
                [],
                None,
            ]
        ] = set()

        self._backfill_anchor: datetime | None = None

        self._backfill_tasks: set[
            asyncio.Task[None]
        ] = set()

    def register_grid_cell(
        self,
        grid_cell: tuple[int, int],
    ) -> None:
        """Register one configured grid cell."""

        self._grid_cell_references[
            grid_cell
        ] = (
            self._grid_cell_references.get(
                grid_cell,
                0,
            )
            + 1
        )

    def unregister_grid_cell(
        self,
        grid_cell: tuple[int, int],
    ) -> None:
        """Unregister one configured grid cell."""

        references = self._grid_cell_references.get(
            grid_cell,
            0,
        )

        if references <= 1:

            self._grid_cell_references.pop(
                grid_cell,
                None,
            )

        else:

            self._grid_cell_references[
                grid_cell
            ] = references - 1

        self._rolling_cache_anchor = None
        self._rolling_cache_grid_cells = ()
        self._rolling_cache = {}

    def register_update_callback(
        self,
        callback: Callable[
            [],
            None,
        ],
    ) -> None:
        """Register a callback for completed background updates."""

        self._update_callbacks.add(
            callback,
        )

    def unregister_update_callback(
        self,
        callback: Callable[
            [],
            None,
        ],
    ) -> None:
        """Unregister a background update callback."""

        self._update_callbacks.discard(
            callback,
        )

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

        grid_cells = tuple(
            sorted(
                self._grid_cell_references
            )
        )

        decoded_rw_by_cell = self._decoder.decode_cells(
            result,
            grid_cells,
        )

        decoded = decoded_rw_by_cell[
            grid_cell
        ]

        decoded_products[
            product.key
        ] = decoded

        latest = decoded.values[-1]

        if result.downloaded:

            await self._history.store(
                result,
            )

            await self._history.prune()

            self._rolling_cache_anchor = None
            self._rolling_cache_grid_cells = ()
            self._rolling_cache = {}

        if (
            self._backfill_anchor
            != latest.valid_until
        ):

            since = (
                latest.valid_until
                - RW.retention
                + RW.interval / 2
            )

            if self._start_backfill(
                since,
            ):
                self._backfill_anchor = (
                    latest.valid_until
                )

        rolling: dict[str, float | None] = {}

        if decoded.values:

            rolling_anchor = (
                decoded.values[0].valid_from
            )

            if (
                self._rolling_cache_anchor
                != rolling_anchor
                or self._rolling_cache_grid_cells
                != grid_cells
            ):

                self._rolling_cache = (
                    await self._history.rolling_summaries_cells(
                        latest_rw=decoded_rw_by_cell,
                    )
                )

                self._rolling_cache_anchor = (
                    rolling_anchor
                )

                self._rolling_cache_grid_cells = (
                    grid_cells
                )

            rolling = self._rolling_cache.get(
                grid_cell,
                {},
            )

        return State(
            decoded_products,
            rolling,
        )

    async def _async_backfill(
        self,
        since: datetime,
    ) -> None:
        """Run RW backfill and notify registered coordinators."""

        (
            completed,
            changed,
        ) = await self._backfill.async_backfill(
            since,
        )

        if not completed:
            self._backfill_anchor = None

        if not changed:
            return

        self._rolling_cache_anchor = None
        self._rolling_cache_grid_cells = ()
        self._rolling_cache = {}

        for callback in tuple(
            self._update_callbacks
        ):
            callback()

    async def async_shutdown(
        self,
    ) -> None:
        """Cancel running background tasks."""

        tasks = tuple(
            self._backfill_tasks
        )

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        self._backfill_tasks.clear()

    def _start_backfill(
        self,
        since: datetime,
    ) -> bool:
        """Start one RW backfill task."""

        if self._backfill_tasks:
            return False

        task = self._hass.async_create_background_task(
            self._async_backfill(
                since,
            ),
            "DWD Rain Radar RW backfill",
        )

        self._backfill_tasks.add(
            task,
        )

        task.add_done_callback(
            self._backfill_tasks.discard,
        )

        return True

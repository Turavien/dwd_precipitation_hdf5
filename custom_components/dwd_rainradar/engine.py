"""Engine for DWD data processing."""

from __future__ import annotations

import asyncio

from collections.abc import Callable

from datetime import (
    UTC,
    datetime,
)

from homeassistant.core import HomeAssistant
from .backfill import Backfill
from .decoder import Decoder
from .fetcher import Fetcher
from .history import History
from .models import (
    DecodedProduct,
    FetchResult,
    ProductMetadata,
)
from .products import (
    Product,
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

        self._decoder = Decoder(
            hass,
        )

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

        self._products = (
            *self._forecast_products,
            RW,
        )

        self._update_lock = asyncio.Lock()

        self._metadata_cache: dict[
            str,
            ProductMetadata,
        ] = {}

        self._latest_product_timestamps: dict[
            str,
            datetime,
        ] = {}

        self._state_cache: dict[
            tuple[int, int],
            State,
        ] = {}

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

        self._state_cache.pop(
            grid_cell,
            None,
        )

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

    async def _async_get_metadata(
        self,
        product: Product,
    ) -> ProductMetadata:
        """Return cached HTTP metadata for one product."""

        cached = self._metadata_cache.get(
            product.key,
        )

        if cached is not None:
            return cached

        metadata = await self._storage.async_read_metadata(
            product.key,
        )

        self._metadata_cache[
            product.key
        ] = metadata

        return metadata

    async def _async_fetch_latest_products(
        self,
    ) -> dict[str, FetchResult]:
        """Check whether newer DWD products are available."""

        results: dict[
            str,
            FetchResult,
        ] = {}

        for product in self._products:

            metadata = await self._async_get_metadata(
                product,
            )

            result = await self._fetcher.async_download(
                product,
                metadata,
                self._latest_product_timestamps.get(
                    product.key,
                ),
            )

            results[
                product.key
            ] = result

        return results

    async def async_update(
        self,
        grid_cell: tuple[int, int],
    ) -> State:
        """Update all configured DWD products."""

        async with self._update_lock:

            remote_results = (
                await self._async_fetch_latest_products()
            )

            if any(
                result.downloaded
                for result in remote_results.values()
            ):
                self._state_cache.clear()

            else:
                cached_state = self._state_cache.get(
                    grid_cell,
                )

                if cached_state is not None:

                    state = cached_state.with_reference_time(
                        datetime.now(
                            UTC,
                        )
                    )

                    self._state_cache[
                        grid_cell
                    ] = state

                    return state

            state = await self._async_build_state(
                grid_cell,
                remote_results,
            )

            self._state_cache[
                grid_cell
            ] = state

            return state

    async def _async_build_state(
        self,
        grid_cell: tuple[int, int],
        remote_results: dict[str, FetchResult],
    ) -> State:
        """Build one state from downloaded or stored products."""

        decoded_products: dict[str, DecodedProduct] = {}

        for product in self._forecast_products:

            result = remote_results[
                product.key
            ]

            if not result.downloaded:

                try:

                    result = await self._storage.async_read_latest_product(
                        product,
                    )

                except FileNotFoundError:

                    result = await self._fetcher.async_download(
                        product,
                        force=True,
                    )

            decoded = await self._decoder.async_decode(
                result,
                grid_cell,
            )

            decoded_products[
                product.key
            ] = decoded

            latest_product_timestamp = (
                decoded.values[0].timestamp
                if decoded.values
                else None
            )

            if result.downloaded:

                await self._storage.async_store_product(
                    result,
                )

            if latest_product_timestamp is not None:
                self._latest_product_timestamps[
                    product.key
                ] = latest_product_timestamp

            self._metadata_cache[
                product.key
            ] = result.metadata

            if result.downloaded:

                await self._storage.async_delete_old_files(
                    product,
                    result.valid_until,
                )

        product = RW

        result = remote_results[
            product.key
        ]

        if not result.downloaded:

            try:

                result = await self._history.read_latest()

            except FileNotFoundError:

                result = await self._fetcher.async_download(
                    product,
                    force=True,
                )

        grid_cells = tuple(
            sorted(
                self._grid_cell_references
            )
        )

        decoded_rw_by_cell = await self._decoder.async_decode_cells(
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

        latest_product_timestamp = (
            decoded.values[0].timestamp
            if decoded.values
            else None
        )

        if result.downloaded:

            await self._history.store(
                result,
            )

        if latest_product_timestamp is not None:
            self._latest_product_timestamps[
                product.key
            ] = latest_product_timestamp

        self._metadata_cache[
            product.key
        ] = result.metadata

        if result.downloaded:

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

        self._state_cache.clear()

        self._rolling_cache_anchor = None
        self._rolling_cache_grid_cells = ()
        self._rolling_cache = {}

        for callback in tuple(
            self._update_callbacks
        ):
            callback()

    def get_diagnostics(
        self,
        state: State | None,
    ) -> dict[str, object]:
        """Return non-sensitive runtime diagnostics."""

        products: dict[str, object] = {}

        for product in self._products:

            timestamp = self._latest_product_timestamps.get(
                product.key,
            )

            metadata = self._metadata_cache.get(
                product.key,
                ProductMetadata(),
            )

            products[
                product.key
            ] = {
                "last_product_timestamp": (
                    timestamp.isoformat()
                    if timestamp is not None
                    else None
                ),
                "fresh": (
                    state.is_product_fresh(
                        product,
                    )
                    if state is not None
                    else None
                ),
                "publication_interval_seconds": int(
                    product.publication_interval.total_seconds()
                ),
                "publication_delay_seconds": int(
                    product.publication_delay.total_seconds()
                ),
                "freshness_window_seconds": int(
                    product.freshness_window.total_seconds()
                ),
                "http_metadata": {
                    "etag": metadata.etag,
                    "last_modified": metadata.last_modified,
                },
            }

        return {
            "products": products,
            "registered_grid_cells": len(
                self._grid_cell_references
            ),
            "config_entry_references": sum(
                self._grid_cell_references.values()
            ),
            "state_cache_entries": len(
                self._state_cache
            ),
            "rolling_cache_entries": len(
                self._rolling_cache
            ),
            "rolling_cache_anchor": (
                self._rolling_cache_anchor.isoformat()
                if self._rolling_cache_anchor is not None
                else None
            ),
            "backfill_anchor": (
                self._backfill_anchor.isoformat()
                if self._backfill_anchor is not None
                else None
            ),
            "backfill_tasks": len(
                self._backfill_tasks
            ),
            "update_callbacks": len(
                self._update_callbacks
            ),
        }

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

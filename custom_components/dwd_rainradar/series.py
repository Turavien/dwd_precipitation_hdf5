"""Generic time series for one DWD product."""

from __future__ import annotations

from datetime import timedelta

from .decoder import Decoder
from .models import (
    DecodedProduct,
    FetchResult,
    TimeInterval,
)
from .products import Product
from .storage import Storage


class Series:
    """Provide history access for a single DWD product."""

    def __init__(
        self,
        storage: Storage,
        decoder: Decoder,
        product: Product,
    ) -> None:
        """Initialize the series."""

        self._storage = storage
        self._decoder = decoder
        self._product = product

        self._intervals: list[
            TimeInterval
        ] | None = None

    async def intervals(
        self,
    ) -> list[
        TimeInterval
    ]:
        """Return all validity intervals."""

        if self._intervals is None:

            self._intervals = sorted(
                (
                    TimeInterval(
                        valid_from=start,
                        valid_until=end,
                    )
                    for start, end in await self._storage.async_list_intervals(
                        self._product,
                    )
                ),
                key=lambda interval: interval.valid_until,
            )

        return self._intervals

    def _invalidate(
        self,
    ) -> None:
        """Invalidate cached data."""

        self._intervals = None

    async def read_interval_cells(
        self,
        interval: TimeInterval,
        grid_cells: tuple[
            tuple[int, int],
            ...
        ],
    ) -> dict[
        tuple[int, int],
        DecodedProduct,
    ]:
        """Read and decode one stored product for multiple grid cells."""

        result = await self._storage.async_read_product(
            self._product,
            interval.valid_from,
        )

        return await self._decoder.async_decode_cells(
            result,
            grid_cells,
        )

    async def read_latest(
        self,
    ) -> FetchResult:
        """Read the newest stored product."""

        return await self._storage.async_read_latest_product(
            self._product,
        )

    async def store(
        self,
        result: FetchResult,
        *,
        update_metadata: bool = True,
    ) -> None:
        """Store a downloaded product."""

        await self._storage.async_store_product(
            result,
            update_metadata=update_metadata,
        )

        self._invalidate()

    async def prune(
        self,
        max_age: timedelta,
    ) -> None:
        """Delete products older than the configured age."""

        intervals = await self.intervals()

        if not intervals:
            return

        latest = intervals[-1]

        await self._storage.async_delete_old_files(
            self._product,
            latest.valid_until - max_age,
        )

        self._invalidate()

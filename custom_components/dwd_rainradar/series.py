"""Generic time series for one DWD product."""

from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
)

from .decoder import Decoder
from .models import (
    DecodedProduct,
    FetchResult,
)
from .products import Product
from .storage import Storage
from .timeline import (
    TimeInterval,
    Timeline,
)


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

        self._timeline: Timeline | None = None

    async def _get_intervals(
        self,
    ) -> list[
        TimeInterval
    ]:
        """Return all validity intervals."""

        if self._intervals is None:

            self._intervals = [
                TimeInterval(
                    valid_from=start,
                    valid_until=end,
                )
                for start, end in await self._storage.async_list_intervals(
                    self._product,
                )
            ]

        return self._intervals

    async def _intervals_before(
        self,
        timestamp: datetime,
        count: int,
    ) -> list[TimeInterval]:
        """Return consecutive intervals ending before a timestamp."""

        intervals = await self.intervals()

        first: TimeInterval | None = None

        for interval in reversed(
            intervals,
        ):

            if interval.valid_until <= timestamp:

                first = interval
                break

        if first is None:
            return []

        selected: list[
            TimeInterval
        ] = [
            first,
        ]

        previous = first

        while len(selected) < count:

            match: TimeInterval | None = next(
                (
                    interval
                    for interval in reversed(
                        intervals,
                    )
                    if interval.valid_until
                    == previous.valid_from
                ),
                None,
            )

            if match is None:

                best_gap: timedelta | None = None

                for interval in reversed(
                    intervals,
                ):

                    if (
                        interval.valid_until
                        > previous.valid_from
                    ):
                        continue

                    gap = (
                        previous.valid_from
                        - interval.valid_until
                    )

                    if (
                        best_gap is None
                        or gap < best_gap
                    ):

                        best_gap = gap
                        match = interval

                        if gap == timedelta():
                            break

            if match is None:
                return []

            selected.append(
                match,
            )

            previous = match

        selected.reverse()

        return selected

    async def intervals(
        self,
    ) -> list[
        TimeInterval
    ]:
        """Return all validity intervals."""

        return await self._get_intervals()

    async def timestamps(
        self,
    ) -> list[datetime]:
        """Return all stored product timestamps."""

        return [
            interval.valid_from
            for interval in await self.intervals()
        ]

    async def timeline(
        self,
    ) -> Timeline:
        """Return the cached timeline."""

        if self._timeline is None:

            self._timeline = Timeline(
                await self.intervals(),
            )

        return self._timeline

    def _invalidate(
        self,
    ) -> None:
        """Invalidate cached data."""

        self._intervals = None
        self._timeline = None

    async def read_interval(
        self,
        interval: TimeInterval,
        grid_cell: tuple[int, int],
    ) -> DecodedProduct:
        """Read and decode one stored product."""

        result = await self._storage.async_read_product(
            self._product,
            interval.valid_from,
        )

        return self._decoder.decode(
            result,
            grid_cell,
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
    ) -> None:
        """Store a downloaded product."""

        await self._storage.async_store_product(
            result,
        )

        self._invalidate()

    async def delete(
        self,
        interval: TimeInterval,
    ) -> None:
        """Delete one stored product."""

        await self._storage.async_delete_product(
            self._product,
            interval.valid_from,
        )

        self._invalidate()

    async def prune(
        self,
        max_age: timedelta,
    ) -> None:
        """Delete products older than the configured age."""

        latest = await self.latest_interval()

        if latest is None:
            return

        await self._storage.async_delete_old_files(
            self._product,
            latest.valid_until - max_age,
        )

        self._invalidate()

    async def latest_interval(
        self,
    ) -> TimeInterval | None:
        """Return the newest validity interval."""

        timeline = await self.timeline()

        return timeline.latest()

    async def hourly_intervals_before(
        self,
        timestamp: datetime,
        count: int,
    ) -> list[TimeInterval]:
        """Return hourly intervals ending immediately before a timestamp."""

        return await self._intervals_before(
            timestamp,
            count,
        )

    async def daily_intervals_before(
        self,
        timestamp: datetime,
        count: int,
    ) -> list[TimeInterval]:
        """Return daily intervals ending immediately before a timestamp."""

        return await self._intervals_before(
            timestamp,
            count,
        )

    async def read_latest_interval(
        self,
        grid_cell: tuple[int, int],
    ) -> DecodedProduct | None:
        """Read and decode the newest stored interval."""

        interval = await self.latest_interval()

        if interval is None:
            return None

        return await self.read_interval(
            interval,
            grid_cell,
        )

    @property
    def product(
        self,
    ) -> Product:
        """Return the associated product."""

        return self._product

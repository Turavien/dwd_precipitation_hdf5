"""Generic time series access for stored DWD products."""

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
from .products import RW
from .series import Series
from .storage import Storage
from .timeline import TimeInterval


class History:
    """Factory for product histories."""

    _ROLLING_WINDOWS = (
        (
            timedelta(),
            timedelta(hours=2),
        ),
        (
            timedelta(),
            timedelta(hours=3),
        ),
        (
            timedelta(),
            timedelta(hours=6),
        ),
        (
            timedelta(),
            timedelta(hours=9),
        ),
        (
            timedelta(),
            timedelta(hours=12),
        ),
        (
            timedelta(),
            timedelta(hours=24),
        ),
        (
            timedelta(),
            timedelta(hours=36),
        ),
        (
            timedelta(),
            timedelta(hours=48),
        ),
    )

    def __init__(
        self,
        storage: Storage,
        decoder: Decoder,
    ) -> None:
        """Initialize the history service."""

        self._series = Series(
            storage,
            decoder,
            RW,
        )

    async def read_latest(
        self,
    ) -> FetchResult:
        """Read the newest stored product."""

        return await self._series.read_latest()

    async def store(
        self,
        result: FetchResult,
    ) -> None:
        """Store a downloaded product."""

        await self._series.store(
            result,
        )

    async def delete(
        self,
        interval: TimeInterval,
    ) -> None:
        """Delete one stored product."""

        await self._series.delete(
            interval,
        )

    async def intervals(
        self,
    ) -> list[
        TimeInterval
    ]:
        """Return all available validity intervals."""

        return await self._series.intervals()

    async def prune(
        self,
    ) -> None:
        """Prune the stored history."""

        await self._series.prune(
            timedelta(
                hours=49,
            ),
        )

    async def intervals_before(
        self,
        timestamp: datetime,
        count: int,
    ) -> list[TimeInterval]:
        """Return a continuous chain of consecutive intervals."""

        tolerance = timedelta(
            minutes=5,
        )

        intervals = await self._series.intervals()

        if not intervals:
            return []

        current_index: int | None = None

        for index in range(
            len(intervals) - 1,
            -1,
            -1,
        ):

            if (
                intervals[index].valid_until
                <= timestamp
            ):
                current_index = index
                break

        if current_index is None:
            return []

        chain = [
            intervals[current_index],
        ]

        while len(chain) < count:

            expected_end = (
                chain[-1].valid_from
            )

            predecessor: TimeInterval | None = None

            for index in range(
                current_index - 1,
                -1,
                -1,
            ):

                candidate = intervals[index]

                delta = abs(
                    candidate.valid_until
                    - expected_end
                )

                if delta <= tolerance:

                    predecessor = candidate
                    current_index = index
                    break

            if predecessor is None:
                break

            chain.append(
                predecessor,
            )

        chain = list(
            reversed(
                chain,
            )
        )

        return chain

    async def rolling_summaries(
        self,
        latest_rw: DecodedProduct,
        grid_cell: tuple[int, int],
    ) -> dict[str, float | None]:
        """Return all rolling precipitation summaries."""

        anchor = latest_rw.values[0].valid_from

        max_hours = max(
            int(
                end_offset.total_seconds()
                // 3600
            )
            for _, end_offset in self._ROLLING_WINDOWS
        )

        intervals = await self.intervals_before(
            anchor,
            max_hours - 1,
        )

        hourly_values: list[
            float | None
        ] = [
            latest_rw.values[0].value,
        ]

        hourly_entries: list[
            tuple[
                datetime,
                datetime,
                float | None,
            ]
        ] = [
            (
                latest_rw.values[0].valid_from,
                latest_rw.values[0].valid_until,
                latest_rw.values[0].value,
            ),
        ]

        for interval in intervals:

            decoded = await self._series.read_interval(
                interval,
                grid_cell,
            )

            value = decoded.values[0]

            hourly_values.append(
                value.value,
            )

            hourly_entries.append(
                (
                    value.valid_from,
                    value.valid_until,
                    value.value,
                )
            )

        result: list[
            float | None
        ] = []

        for _, end_offset in self._ROLLING_WINDOWS:

            hours = int(
                end_offset.total_seconds()
                // 3600
            )

            if len(
                hourly_values,
            ) < hours:

                result.append(
                    None,
                )

                continue

            window = hourly_values[
                :hours
            ]

            if any(
                value is None
                for value in window
            ):

                result.append(
                    None,
                )

                continue

            total = sum(
                window,
            )

            result.append(
                total,
            )

        (
            rw_2h,
            rw_3h,
            rw_6h,
            rw_9h,
            rw_12h,
            rw_24h,
            rw_36h,
            rw_48h,
        ) = tuple(
            result,
        )

        return {
            "rw_2h": rw_2h,
            "rw_3h": rw_3h,
            "rw_6h": rw_6h,
            "rw_9h": rw_9h,
            "rw_12h": rw_12h,
            "rw_24h": rw_24h,
            "rw_36h": rw_36h,
            "rw_48h": rw_48h,
        }


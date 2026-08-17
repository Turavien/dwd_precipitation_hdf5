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
    TimeInterval,
)
from .products import RW
from .series import Series
from .storage import Storage


class History:
    """Factory for product histories."""

    _ROLLING_WINDOWS = (
        ("rw_2h", 2),
        ("rw_3h", 3),
        ("rw_6h", 6),
        ("rw_9h", 9),
        ("rw_12h", 12),
        ("rw_24h", 24),
        ("rw_36h", 36),
        ("rw_48h", 48),
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
        *,
        update_metadata: bool = True,
    ) -> None:
        """Store a downloaded product."""

        await self._series.store(
            result,
            update_metadata=update_metadata,
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
            RW.retention,
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

        chain.reverse()

        return chain

    async def rolling_summaries_cells(
        self,
        latest_rw: dict[
            tuple[int, int],
            DecodedProduct,
        ],
    ) -> dict[
        tuple[int, int],
        dict[str, float | None],
    ]:
        """Return rolling precipitation summaries for multiple grid cells."""

        if not latest_rw:
            return {}

        first_latest = next(
            iter(
                latest_rw.values(),
            )
        )

        if not first_latest.values:
            return {}

        anchor = first_latest.values[0].valid_from

        for decoded in latest_rw.values():

            if not decoded.values:
                return {}

            if (
                decoded.values[0].valid_from
                != anchor
            ):
                raise ValueError(
                    "RW grid cells do not share the same validity interval."
                )

        max_hours = max(
            hours
            for _, hours in self._ROLLING_WINDOWS
        )

        intervals = await self.intervals_before(
            anchor,
            max_hours - 1,
        )

        grid_cells = tuple(
            latest_rw.keys()
        )

        hourly_values: dict[
            tuple[int, int],
            list[float | None],
        ] = {
            grid_cell: [
                decoded.values[0].value,
            ]
            for grid_cell, decoded in latest_rw.items()
        }

        for interval in reversed(
            intervals,
        ):

            decoded_by_cell = (
                await self._series.read_interval_cells(
                    interval,
                    grid_cells,
                )
            )

            for grid_cell in grid_cells:

                decoded = decoded_by_cell[
                    grid_cell
                ]

                hourly_values[
                    grid_cell
                ].append(
                    decoded.values[0].value,
                )

        summaries: dict[
            tuple[int, int],
            dict[str, float | None],
        ] = {}

        for grid_cell in grid_cells:

            values = hourly_values[
                grid_cell
            ]

            cell_summary: dict[
                str,
                float | None,
            ] = {}

            for key, hours in self._ROLLING_WINDOWS:

                if len(
                    values,
                ) < hours:

                    cell_summary[
                        key
                    ] = None

                    continue

                window = values[
                    :hours
                ]

                if any(
                    value is None
                    for value in window
                ):

                    cell_summary[
                        key
                    ] = None

                    continue

                cell_summary[
                    key
                ] = sum(
                    window,
                )

            summaries[
                grid_cell
            ] = cell_summary

        return summaries

"""Generic time series access for stored DWD products."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from datetime import (
    datetime,
    timedelta,
)

from .decoder import Decoder
from .models import (
    DecodedProduct,
    FetchResult,
)
from .products import (
    Product,
    RW,
)
from .rolling import rolling_sum
from .series import Series
from .storage import Storage
from .timeline import (
    ResolveStrategy,
    ResolvedInterval,
    TimeInterval,
    Timeline,
)


@dataclass(frozen=True, slots=True)
class HistoricalProduct:
    """Decoded product together with its resolved interval."""

    resolved: ResolvedInterval
    product: DecodedProduct


@dataclass(frozen=True, slots=True)
class HistoryResult:
    """Collection of historical products."""

    products: tuple[HistoricalProduct, ...]

    def __iter__(
        self,
    ) -> Iterator[HistoricalProduct]:
        """Iterate over historical products."""

        return iter(
            self.products,
        )

    def __len__(
        self,
    ) -> int:
        """Return the number of historical products."""

        return len(
            self.products,
        )


class ProductHistory:
    """History access for one DWD product."""

    def __init__(
        self,
        series: Series,
    ) -> None:
        """Initialize the product history."""

        self._series = series

    async def timeline(
        self,
    ) -> Timeline:
        """Return the timeline."""

        return await self._series.timeline()

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

    async def prune(
        self,
        max_age: timedelta,
    ) -> None:
        """Delete products older than the configured age."""

        await self._series.prune(
            max_age,
        )

    async def latest_interval(
        self,
    ) -> TimeInterval | None:
        """Return the newest available validity interval."""

        return await self._series.latest_interval()

    async def intervals(
        self,
    ) -> list[
        tuple[datetime, datetime]
    ]:
        """Return all available validity intervals."""

        return await self._series.intervals()

    async def resolved_targets(
        self,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> list[ResolvedInterval]:
        """Return resolved intervals for a time range."""

        timeline = await self.timeline()

        targets = timeline.generate_targets(
            anchor,
            self._series.product.interval,
            start_offset,
            end_offset,
        )

        return timeline.resolve_targets(
            targets,
            strategy,
        )

    async def historical_products(
        self,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        grid_cell: tuple[int, int],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> HistoryResult:
        """Return historical products for a time range."""

        return HistoryResult(
            products=tuple(
                await self.read_resolved_targets(
                    await self.resolved_targets(
                        anchor,
                        start_offset,
                        end_offset,
                        strategy,
                    ),
                    grid_cell,
                )
            ),
        )

    async def rolling_sum(
        self,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        grid_cell: tuple[int, int],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> float | None:
        """Return the rolling precipitation sum."""

        if self._series.product.key == "rw":

            hours = int(
                (
                    end_offset
                    - start_offset
                ).total_seconds()
                // 3600
            )

            intervals = await self._series.hourly_intervals_before(
                anchor,
                hours,
            )

            if len(intervals) != hours:
                return None

            total = 0.0

            for interval in intervals:

                decoded = await self._series.read_interval(
                    interval,
                    grid_cell,
                )

                total += (
                    decoded.values[0].value
                    or 0.0
                )

            return total

        return rolling_sum(
            await self.historical_products(
                anchor,
                start_offset,
                end_offset,
                grid_cell,
                strategy,
            ),
        )

    async def rolling_summaries(
        self,
        anchor: datetime,
        grid_cell: tuple[int, int],
        windows: tuple[tuple[timedelta, timedelta], ...],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> tuple[float | None, ...]:
        """Return multiple rolling precipitation sums."""

        if self._series.product.key != "rw":

            result: list[float | None] = []

            for start_offset, end_offset in windows:

                result.append(
                    await self.rolling_sum(
                        anchor,
                        start_offset,
                        end_offset,
                        grid_cell,
                        strategy,
                    ),
                )

            return tuple(
                result,
            )

        max_hours = max(
            int(
                end_offset.total_seconds()
                // 3600
            )
            for _, end_offset in windows
        )

        intervals = await self._series.hourly_intervals_before(
            anchor,
            max_hours,
        )

        if len(
            intervals,
        ) != max_hours:

            return tuple(
                None
                for _ in windows
            )

        hourly_values: list[float] = []

        for interval in intervals:

            decoded = await self._series.read_interval(
                interval,
                grid_cell,
            )

            hourly_values.append(
                decoded.values[0].value
                or 0.0
            )

        result: list[float | None] = []

        for _, end_offset in windows:

            hours = int(
                end_offset.total_seconds()
                // 3600
            )

            result.append(
                sum(
                    hourly_values[
                        :hours
                    ]
                )
            )

        return tuple(
            result,
        )

    async def read_resolved(
        self,
        resolved: ResolvedInterval,
        grid_cell: tuple[int, int],
    ) -> HistoricalProduct | None:
        """Read one resolved interval."""

        if resolved.interval is None:
            return None

        return HistoricalProduct(
            resolved=resolved,
            product=await self._series.read_interval(
                resolved.interval,
                grid_cell,
            ),
        )

    async def read_resolved_targets(
        self,
        resolved_targets: list[ResolvedInterval],
        grid_cell: tuple[int, int],
    ) -> list[HistoricalProduct]:
        """Read multiple resolved intervals."""

        result: list[HistoricalProduct] = []

        for resolved in resolved_targets:

            product = await self.read_resolved(
                resolved,
                grid_cell,
            )

            if product is not None:

                result.append(
                    product,
                )

        return result


class History:
    """Factory for product histories."""

    def __init__(
        self,
        storage: Storage,
        decoder: Decoder,
    ) -> None:
        """Initialize the history service."""

        self._storage = storage
        self._decoder = decoder
        self._history: dict[str, ProductHistory] = {}

    def product(
        self,
        product: Product,
    ) -> ProductHistory:
        """Return the history for one product."""

        history = self._history.get(
            product.key,
        )

        if history is None:

            history = ProductHistory(
                Series(
                    self._storage,
                    self._decoder,
                    product,
                ),
            )

            self._history[
                product.key
            ] = history

        return history

    async def prune(
        self,
    ) -> None:
        """Prune the stored history."""

        await self.product(
            RW,
        ).prune(
            timedelta(
                hours=49,
            ),
        )

    async def delete(
        self,
        product: Product,
        interval: TimeInterval,
    ) -> None:
        """Delete one stored product."""

        await self.product(
            product,
        ).delete(
            interval,
        )

    async def timeline(
        self,
        product: Product,
    ) -> Timeline:
        """Return the timeline for one product."""

        return await self.product(
            product,
        ).timeline()

    async def resolved_targets(
        self,
        product: Product,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> list[ResolvedInterval]:
        """Return resolved intervals for a time range."""

        return await self.product(
            product,
        ).resolved_targets(
            anchor,
            start_offset,
            end_offset,
            strategy,
        )

    async def historical_products(
        self,
        product: Product,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        grid_cell: tuple[int, int],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> HistoryResult:
        """Return historical products for a time range."""

        return await self.product(
            product,
        ).historical_products(
            anchor,
            start_offset,
            end_offset,
            grid_cell,
            strategy,
        )

    async def rolling_sum(
        self,
        product: Product,
        anchor: datetime,
        start_offset: timedelta,
        end_offset: timedelta,
        grid_cell: tuple[int, int],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> float | None:
        """Return the rolling precipitation sum."""

        return await self.product(
            product,
        ).rolling_sum(
            anchor,
            start_offset,
            end_offset,
            grid_cell,
            strategy,
        )

    async def rolling_summaries(
        self,
        rw_anchor: datetime,
        grid_cell: tuple[int, int],
    ) -> dict[str, float |None]:
        """Return all rolling precipitation summaries."""

        (
            rw_2h,
            rw_3h,
            rw_6h,
            rw_9h,
            rw_12h,
            rw_24h,
            rw_36h,
            rw_48h,
        ) = await self.product(
            RW,
        ).rolling_summaries(
            anchor=rw_anchor,
            grid_cell=grid_cell,
            windows=(
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
            ),
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

    async def read_resolved(
        self,
        product: Product,
        resolved: ResolvedInterval,
        grid_cell: tuple[int, int],
    ) -> HistoricalProduct | None:
        """Read one resolved interval."""

        return await self.product(
            product,
        ).read_resolved(
            resolved,
            grid_cell,
        )

    async def read_resolved_targets(
        self,
        product: Product,
        resolved_targets: list[ResolvedInterval],
        grid_cell: tuple[int, int],
    ) -> list[HistoricalProduct]:
        """Read multiple resolved intervals."""

        return await self.product(
            product,
        ).read_resolved_targets(
            resolved_targets,
            grid_cell,
        )

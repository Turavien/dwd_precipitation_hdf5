"""Utilities for working with product timelines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
)
from enum import Enum


class ResolveStrategy(Enum):
    """Timestamp resolution strategy."""

    EXACT = "exact"
    PREVIOUS = "previous"
    NEXT = "next"
    NEAREST = "nearest"


@dataclass(frozen=True, slots=True)
class TimeInterval:
    """Validity interval of one stored product."""

    valid_from: datetime

    valid_until: datetime


@dataclass(frozen=True, slots=True)
class TargetInterval:
    """Requested validity interval."""

    valid_from: datetime

    valid_until: datetime


@dataclass(frozen=True, slots=True)
class ResolvedInterval:
    """Resolved validity interval."""

    target: TargetInterval

    interval: TimeInterval | None


class Timeline:
    """Provide timestamp lookup utilities."""

    def __init__(
        self,
        intervals: list[TimeInterval],
    ) -> None:
        """Initialize the timeline."""

        self._intervals = sorted(
            intervals,
            key=lambda interval: (
                interval.valid_from,
            ),
        )

    @property
    def intervals(
        self,
    ) -> list[TimeInterval]:
        """Return all validity intervals."""

        return self._intervals

    def latest(
        self,
    ) -> TimeInterval | None:
        """Return the newest validity interval."""

        if not self._intervals:
            return None

        return max(
            self._intervals,
            key=lambda interval: (
                interval.valid_until,
            ),
        )

    def _overlap(
        self,
        target: TargetInterval,
        interval: TimeInterval,
    ) -> timedelta:
        """Return the overlap between two intervals."""

        start = max(
            target.valid_from,
            interval.valid_from,
        )

        end = min(
            target.valid_until,
            interval.valid_until,
        )

        if end <= start:
            return timedelta()

        return end - start

    def _overlapping_intervals(
        self,
        target: TargetInterval,
    ):
        """Yield all overlapping intervals together with their overlap."""

        for interval in self._intervals:

            overlap = self._overlap(
                target,
                interval,
            )

            if overlap > timedelta():

                yield (
                    interval,
                    overlap,
                )

    def _score(
        self,
        target: TargetInterval,
        interval: TimeInterval,
        overlap: timedelta,
    ) -> tuple[
        timedelta,
        timedelta,
        timedelta,
        float,
    ]:
        """Return the matching score for one interval."""

        return (
            overlap,
            -abs(
                interval.valid_from
                - target.valid_from
            ),
            -abs(
                interval.valid_until
                - target.valid_until
            ),
            interval.valid_from.timestamp(),
        )

    def _find_interval(
        self,
        target: TargetInterval,
    ) -> TimeInterval | None:
        """Return the best matching interval."""

        best: TimeInterval | None = None

        best_score: (
            tuple[
                timedelta,
                timedelta,
                timedelta,
                float,
            ]
            | None
        ) = None

        for (
            interval,
            overlap,
        ) in self._overlapping_intervals(
            target,
        ):

            score = self._score(
                target,
                interval,
                overlap,
            )

            if (
                best_score is None
                or score > best_score
            ):

                best = interval
                best_score = score

        return best

    def _earliest_after(
        self,
        target: TargetInterval,
    ) -> TimeInterval | None:
        """Return the first interval beginning after the requested interval."""

        return next(
            (
                interval
                for interval in self._intervals
                if interval.valid_from
                >= target.valid_until
            ),
            None,
        )

    def generate_targets(
        self,
        reference: datetime,
        interval: timedelta,
        start_offset: timedelta,
        end_offset: timedelta,
    ) -> list[TargetInterval]:
        """Generate requested validity intervals."""

        first = start_offset // interval
        last = end_offset // interval

        return [
            TargetInterval(
                valid_from=(
                    reference
                    - interval * (offset + 1)
                ),
                valid_until=(
                    reference
                    - interval * offset
                ),
            )
            for offset in range(
                first,
                last,
            )
        ]

    def resolve_targets(
        self,
        targets: list[TargetInterval],
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> list[ResolvedInterval]:
        """Resolve multiple target intervals."""

        resolved: list[
            ResolvedInterval
        ] = []

        used: set[
            TimeInterval
        ] = set()

        for target in targets:

            interval = self.resolve(
                target,
                strategy,
            )

            if interval is not None:

                if interval in used:
                    interval = None

                else:
                    used.add(
                        interval,
                    )

            resolved.append(
                ResolvedInterval(
                    target=target,
                    interval=interval,
                )
            )

        return resolved

    def resolve(
        self,
        target: TargetInterval,
        strategy: ResolveStrategy = ResolveStrategy.PREVIOUS,
    ) -> TimeInterval | None:
        """Resolve one requested interval to a stored interval."""

        if strategy in (
            ResolveStrategy.EXACT,
            ResolveStrategy.PREVIOUS,
        ):

            return self._find_interval(
                target,
            )

        if strategy is ResolveStrategy.NEXT:
            return self._earliest_after(
                target,
            )

        previous = self._find_interval(
            target,
        )

        following = self._earliest_after(
            target,
        )

        if previous is None or following is None:
            return previous or following

        if (
            target.valid_from
            - previous.valid_from
            <= following.valid_from
            - target.valid_from
        ):
            return previous

        return following


"""Current state of the DWD Rain Radar integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from math import ceil

from .models import (
    DecodedProduct,
    ParsedValue,
)
from .products import Product


@dataclass(frozen=True, slots=True)
class State:
    """Current processed state of all DWD products."""

    _products: dict[str, DecodedProduct]

    _rolling: dict[str, float | None]

    _reference_time: datetime = field(
        default_factory=lambda: datetime.now(
            UTC,
        )
    )

    def with_reference_time(
        self,
        reference_time: datetime,
    ) -> State:
        """Return the same data evaluated at a new real-world time."""

        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(
                tzinfo=UTC,
            )
        else:
            reference_time = reference_time.astimezone(
                UTC,
            )

        return State(
            self._products,
            self._rolling,
            reference_time,
        )

    def is_product_fresh(
        self,
        product: Product,
    ) -> bool:
        """Return whether one DWD product is still current."""

        values = self._values(
            product.key,
        )

        if not values:
            return False

        latest_timestamp = max(
            value.timestamp
            for value in values
        )

        return (
            self._reference_time
            <= latest_timestamp
            + product.freshness_window
        )

    def _values(
        self,
        key: str,
    ) -> tuple[ParsedValue, ...]:
        """Return parsed values of one product."""

        product = self._products.get(
            key,
        )

        if product is None:
            return ()

        return product.values

    def _last(
        self,
        key: str,
    ) -> ParsedValue | None:
        """Return the last parsed value of one product."""

        values = self._values(
            key,
        )

        if not values:
            return None

        return values[-1]

    def _end_offset_minutes(
        self,
        value: ParsedValue,
    ) -> int:
        """Return the forecast interval end offset in minutes."""

        return int(
            (
                value.valid_until
                - value.timestamp
            ).total_seconds()
            / 60
        )

    def _sum_rs_hours(
        self,
        hours: int,
    ) -> float | None:
        """Return precipitation for consecutive future RS hours."""

        total = 0.0

        for hour in range(
            1,
            hours + 1,
        ):
            value = self._number_by_end_offset(
                "rs",
                hour * 60,
            )

            if value is None:
                return None

            total += value

        return total

    def _number_by_end_offset(
        self,
        key: str,
        offset_minutes: int,
    ) -> float | None:
        """Return one forecast value by interval end offset."""

        for value in self._values(
            key,
        ):
            if (
                self._end_offset_minutes(
                    value,
                )
                == offset_minutes
            ):
                return value.value

        return None

    def _value_at_time(
        self,
        key: str,
        target_time: datetime,
    ) -> ParsedValue | None:
        """Return the value whose validity interval contains one time."""

        for value in self._values(
            key,
        ):
            if (
                value.valid_from
                <= target_time
                < value.valid_until
            ):
                return value

        return None

    def _rv_intensity_at_offset(
        self,
        offset_minutes: int,
    ) -> float | None:
        """Return RV intensity for a real-time offset."""

        target_time = (
            self._reference_time
            + timedelta(
                minutes=offset_minutes,
            )
        )

        value = self._value_at_time(
            "rv",
            target_time,
        )

        if (
            value is None
            or value.value is None
        ):
            return None

        return value.value * 12

    def _maximum_rv_intensity(
        self,
    ) -> float | None:
        """Return maximum RV intensity in the available next two hours."""

        window_start = self._reference_time

        window_end = (
            window_start
            + timedelta(
                hours=2,
            )
        )

        maximum: float | None = None

        for value in self._values(
            "rv",
        ):
            if (
                value.valid_until
                <= window_start
                or value.valid_from
                >= window_end
            ):
                continue

            if value.value is None:
                return None

            if (
                maximum is None
                or value.value > maximum
            ):
                maximum = value.value

        if maximum is None:
            return None

        return maximum * 12

    def _first_positive_rv_start_minutes(
        self,
    ) -> int | None:
        """Return real minutes until the next positive RV interval starts."""

        for value in self._values(
            "rv",
        ):
            if (
                value.valid_until
                <= self._reference_time
            ):
                continue

            if value.value is None:
                return None

            if value.value <= 0.0:
                continue

            if (
                value.valid_from
                <= self._reference_time
                < value.valid_until
            ):
                return 0

            seconds_until_start = (
                value.valid_from
                - self._reference_time
            ).total_seconds()

            return max(
                0,
                ceil(
                    seconds_until_start
                    / 60
                ),
            )

        return None

    @property
    def precipitation_last_1h(
        self,
    ) -> float | None:
        """Return precipitation during the last hour."""

        latest = self._last(
            "rw",
        )

        if latest is None:
            return None

        return latest.value

    @property
    def precipitation_last_2h(
        self,
    ) -> float | None:
        """Return precipitation during the last two hours."""

        return self._rolling.get(
            "rw_2h",
        )

    @property
    def precipitation_last_3h(
        self,
    ) -> float | None:
        """Return precipitation during the last three hours."""

        return self._rolling.get(
            "rw_3h",
        )

    @property
    def precipitation_last_6h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 6 hours."""

        return self._rolling.get(
            "rw_6h",
        )

    @property
    def precipitation_last_9h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 9 hours."""

        return self._rolling.get(
            "rw_9h",
        )

    @property
    def precipitation_last_12h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 12 hours."""

        return self._rolling.get(
            "rw_12h",
        )

    @property
    def precipitation_last_24h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 24 hours."""

        return self._rolling.get(
            "rw_24h",
        )

    @property
    def precipitation_last_36h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 36 hours."""

        return self._rolling.get(
            "rw_36h",
        )

    @property
    def precipitation_last_48h(
        self,
    ) -> float | None:
        """Return the precipitation during the last 48 hours."""

        return self._rolling.get(
            "rw_48h",
        )

    @property
    def precipitation_next_1h(
        self,
    ) -> float | None:
        """Return forecast precipitation during the next hour."""

        return self._sum_rs_hours(
            1,
        )

    @property
    def precipitation_next_2h(
        self,
    ) -> float | None:
        """Return forecast precipitation during the next two hours."""

        return self._sum_rs_hours(
            2,
        )

    @property
    def intensity_now(
        self,
    ) -> float | None:
        """Return intensity for the RV interval containing the current time."""

        return self._rv_intensity_at_offset(
            0,
        )

    @property
    def precipitation_active(
        self,
    ) -> bool | None:
        """Return whether precipitation is present at the current time."""

        value = self._value_at_time(
            "rv",
            self._reference_time,
        )

        if (
            value is None
            or value.value is None
        ):
            return None

        return value.value > 0.0

    @property
    def intensity_in_5min(
        self,
    ) -> float | None:
        """Return intensity for the RV interval containing now plus 5 minutes."""

        return self._rv_intensity_at_offset(
            5,
        )

    @property
    def intensity_in_10min(
        self,
    ) -> float | None:
        """Return intensity for the RV interval containing now plus 10 minutes."""

        return self._rv_intensity_at_offset(
            10,
        )

    @property
    def intensity_in_15min(
        self,
    ) -> float | None:
        """Return intensity for the RV interval containing now plus 15 minutes."""

        return self._rv_intensity_at_offset(
            15,
        )

    @property
    def maximum_precipitation_intensity(
        self,
    ) -> float | None:
        """Return maximum available RV intensity from the current time onward."""

        return self._maximum_rv_intensity()

    @property
    def precipitation_start(
        self,
    ) -> int | None:
        """Return real minutes until precipitation is expected."""

        return self._first_positive_rv_start_minutes()

    @property
    def rw(
        self,
    ) -> tuple[ParsedValue, ...]:
        """Return RADOLAN-RW values."""

        return self._values(
            "rw",
        )


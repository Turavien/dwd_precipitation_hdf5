"""Current state of the DWD Rain Radar integration."""

from __future__ import annotations

from dataclasses import dataclass

from .models import (
    DecodedProduct,
    ParsedValue,
)


@dataclass(frozen=True, slots=True)
class State:
    """Current processed state of all DWD products."""

    _products: dict[str, DecodedProduct]

    _rolling: dict[str, float | None]

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

    def _rv_intensity_by_end_offset(
        self,
        offset_minutes: int,
    ) -> float | None:
        """Return RV precipitation intensity by interval end offset."""

        value = self._number_by_end_offset(
            "rv",
            offset_minutes,
        )

        if value is None:
            return None

        return value * 12

    def _maximum_by_end_offset(
        self,
        key: str,
        minimum_offset_minutes: int = 0,
    ) -> float | None:
        """Return the maximum forecast value from one end offset."""

        maximum: float | None = None

        for value in self._values(
            key,
        ):
            offset = self._end_offset_minutes(
                value,
            )

            if offset < minimum_offset_minutes:
                continue

            if value.value is None:
                return None

            if (
                maximum is None
                or value.value > maximum
            ):
                maximum = value.value

        return maximum

    def _first_positive_rv_end_offset(
        self,
        minimum_offset_minutes: int = 0,
    ) -> int | None:
        """Return the first RV interval end offset with precipitation."""

        for value in self._values(
            "rv",
        ):
            offset = self._end_offset_minutes(
                value,
            )

            if offset < minimum_offset_minutes:
                continue

            if value.value is None:
                return None

            if value.value > 0.0:
                return offset

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
        """Return intensity for the five-minute interval ending now."""

        return self._rv_intensity_by_end_offset(
            0,
        )

    @property
    def precipitation_active(
        self,
    ) -> bool | None:
        """Return whether precipitation is present in the current RV interval."""

        value = self._number_by_end_offset(
            "rv",
            0,
        )

        if value is None:
            return None

        return value > 0.0

    @property
    def intensity_in_5min(
        self,
    ) -> float | None:
        """Return intensity for the interval ending in five minutes."""

        return self._rv_intensity_by_end_offset(
            5,
        )

    @property
    def intensity_in_10min(
        self,
    ) -> float | None:
        """Return intensity for the interval ending in ten minutes."""

        return self._rv_intensity_by_end_offset(
            10,
        )

    @property
    def intensity_in_15min(
        self,
    ) -> float | None:
        """Return intensity for the interval ending in fifteen minutes."""

        return self._rv_intensity_by_end_offset(
            15,
        )

    @property
    def maximum_precipitation_intensity(
        self,
    ) -> float | None:
        """Return the maximum forecast precipitation intensity."""

        maximum = self._maximum_by_end_offset(
            "rv",
            5,
        )

        if maximum is None:
            return None

        return maximum * 12

    @property
    def precipitation_start(
        self,
    ) -> int | None:
        """Return minutes until precipitation is expected."""

        return self._first_positive_rv_end_offset(
            0,
        )

    @property
    def rw(
        self,
    ) -> tuple[ParsedValue, ...]:
        """Return RADOLAN-RW values."""

        return self._values(
            "rw",
        )


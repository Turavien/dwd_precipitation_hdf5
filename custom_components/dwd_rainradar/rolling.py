"""Rolling precipitation calculations."""

from __future__ import annotations

from .storage import RainHistoryStorage


class RainRollingCalculator:
    """Calculate derived rolling precipitation values."""

    def __init__(
        self,
        history: RainHistoryStorage,
    ) -> None:

        self._history = history

    def calculate(self) -> dict[str, float | None]:
        """Return all derived values."""

        data: dict[str, float | None] = {}

        data.update(
            self._calculate_rw()
        )

        data.update(
            self._calculate_sf()
        )

        return data

    def _calculate_rw(
        self,
    ) -> dict[str, float | None]:
        """Return rolling RW precipitation sums."""

        timestamp = self._history.latest_timestamp

        if timestamp is None:

            return {
                "rw_2h": None,
                "rw_3h": None,
                "rw_6h": None,
                "rw_12h": None,
            }

        return {

            "rw_2h": self._history.rolling_sum(
                timestamp,
                2,
            ),

            "rw_3h": self._history.rolling_sum(
                timestamp,
                3,
            ),

            "rw_6h": self._history.rolling_sum(
                timestamp,
                6,
            ),

            "rw_12h": self._history.rolling_sum(
                timestamp,
                12,
            ),
        }

    def _calculate_sf(
        self,
    ) -> dict[str, float | None]:
        """Return extended precipitation sums based on SF history."""

        sf_now = self._history.get_sf_value(0)

        if sf_now is None:

            return {
                "sf_36h": None,
                "sf_48h": None,
                "sf_72h": None,
            }

        rw_25_36h = self._history.sum_rw_range(
            25,
            36,
        )

        sf_24h = self._history.get_sf_value(24)

        sf_48h = self._history.get_sf_value(48)

        return {

            "sf_36h": (
                sf_now + rw_25_36h
                if rw_25_36h is not None
                else None
            ),

            "sf_48h": (
                sf_now + sf_24h
                if sf_24h is not None
                else None
            ),

            "sf_72h": (
                sf_now + sf_24h + sf_48h
                if (
                    sf_24h is not None
                    and sf_48h is not None
                )
                else None
            ),
        }


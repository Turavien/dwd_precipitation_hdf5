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

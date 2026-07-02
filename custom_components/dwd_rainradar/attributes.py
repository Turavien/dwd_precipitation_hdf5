"""Sensor attribute helpers."""

from __future__ import annotations

from .coordinator import UpdateCoordinator


class RainAttributes:
    """Build sensor attributes."""

    @staticmethod
    def rw(
        coordinator: UpdateCoordinator,
    ) -> dict[str, object]:
        """Return attributes for RW sensors."""

        history = coordinator.history

        return {

            "product": "RW",

            "source": "RADOLAN",

            "latest_measurement": (
                history.latest_timestamp
            ),

            "history_entries": (
                len(history.entries)
            ),

        }

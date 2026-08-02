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

        latest_measurement = None

        if coordinator.data.rw:
            latest_measurement = (
                coordinator.data.rw[0].timestamp
            )

        return {

            "product": "RW",

            "source": "RADOLAN",

            "latest_measurement": (
                latest_measurement
            ),

            "history_entries": (
                len(
                    coordinator.data.rw,
                )
            ),

        }


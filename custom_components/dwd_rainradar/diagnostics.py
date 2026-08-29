"""Diagnostics for DWD Rain Radar."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics for one config entry."""

    coordinator = entry.runtime_data.coordinator

    last_exception = coordinator.last_exception

    sensor_groups = entry.options.get(
        CONF_SENSOR_GROUPS,
        entry.data.get(
            CONF_SENSOR_GROUPS,
            DEFAULT_SENSOR_GROUPS,
        ),
    )

    return {
        "config_entry": {
            "version": entry.version,
            "minor_version": entry.minor_version,
            "sensor_groups": list(
                sensor_groups
            ),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": (
                type(
                    last_exception
                ).__name__
                if last_exception is not None
                else None
            ),
            "update_interval_seconds": (
                int(
                    coordinator.update_interval.total_seconds()
                )
                if coordinator.update_interval is not None
                else None
            ),
        },
        "runtime": coordinator.get_diagnostics(),
    }

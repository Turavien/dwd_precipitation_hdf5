"""Test DWD Rain Radar config-entry diagnostics."""

from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.dwd_rainradar import MyData
from custom_components.dwd_rainradar.const import (
    CONF_SENSOR_GROUPS,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
)
from custom_components.dwd_rainradar.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_config_entry_diagnostics_exclude_location(
    hass: HomeAssistant,
) -> None:
    """Test diagnostics expose useful status without location data."""

    coordinator = MagicMock()

    coordinator.last_update_success = True
    coordinator.last_exception = RuntimeError(
        "test failure"
    )
    coordinator.update_interval = timedelta(
        seconds=30,
    )
    coordinator.get_diagnostics.return_value = {
        "products": {
            "rw": {
                "fresh": True,
            },
        },
    }

    entry = MagicMock()

    entry.version = 1
    entry.minor_version = 5
    entry.runtime_data = MyData(
        coordinator,
    )

    entry.options = {
        CONF_SENSOR_GROUPS: [
            SENSOR_GROUP_CURRENT,
            SENSOR_GROUP_EVENT,
        ],
    }

    entry.data = {
        "name": "Private location",
        "latitude": 52.5,
        "longitude": 13.4,
        "grid_cell": (416, 784),
    }

    diagnostics = await async_get_config_entry_diagnostics(
        hass,
        entry,
    )

    assert diagnostics == {
        "config_entry": {
            "version": 1,
            "minor_version": 5,
            "sensor_groups": [
                SENSOR_GROUP_CURRENT,
                SENSOR_GROUP_EVENT,
            ],
        },
        "coordinator": {
            "last_update_success": True,
            "last_exception": "RuntimeError",
            "update_interval_seconds": 30,
        },
        "runtime": {
            "products": {
                "rw": {
                    "fresh": True,
                },
            },
        },
    }

    diagnostic_text = repr(
        diagnostics,
    )

    assert "Private location" not in diagnostic_text
    assert "52.5" not in diagnostic_text
    assert "13.4" not in diagnostic_text
    assert "416" not in diagnostic_text
    assert "784" not in diagnostic_text

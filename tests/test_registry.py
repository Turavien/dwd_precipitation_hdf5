"""Test DWD Rain Radar entity-registry cleanup."""

from unittest.mock import MagicMock, patch

from custom_components.dwd_rainradar.const import (
    CONF_SENSOR_GROUPS,
    SENSOR_GROUP_CURRENT,
)
from custom_components.dwd_rainradar.registry import (
    async_remove_disabled_entities,
)


async def test_remove_disabled_entities() -> None:
    """Test inactive entity-registry entries are removed."""

    hass = MagicMock()
    entry = MagicMock()

    entry.entry_id = "test-entry-id"
    entry.options = {}
    entry.data = {
        CONF_SENSOR_GROUPS: [
            SENSOR_GROUP_CURRENT,
        ],
    }

    active = MagicMock()
    active.unique_id = (
        "test-entry-id_radvor_rv_now"
    )
    active.entity_id = "sensor.active"

    inactive = MagicMock()
    inactive.unique_id = (
        "test-entry-id_radvor_rv_start"
    )
    inactive.entity_id = "sensor.inactive"

    registry = MagicMock()

    with (
        patch(
            "custom_components.dwd_rainradar.registry."
            "er.async_get",
            return_value=registry,
        ),
        patch(
            "custom_components.dwd_rainradar.registry."
            "er.async_entries_for_config_entry",
            return_value=[
                active,
                inactive,
            ],
        ),
    ):
        await async_remove_disabled_entities(
            hass,
            entry,
        )

    registry.async_remove.assert_called_once_with(
        "sensor.inactive",
    )

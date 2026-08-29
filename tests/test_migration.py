"""Test config-entry migration for DWD Rain Radar."""

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dwd_rainradar import async_migrate_entry
from custom_components.dwd_rainradar.const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
)


async def test_migrate_minor_4_sensor_groups_to_options(
    hass: HomeAssistant,
) -> None:
    """Test migration of sensor groups from data to options."""

    selected_groups = [
        SENSOR_GROUP_CURRENT,
        SENSOR_GROUP_EVENT,
    ]

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=4,
        data={
            "name": "Test",
            "latitude": 52.52,
            "longitude": 13.405,
            "grid_cell": (416, 784),
            CONF_SENSOR_GROUPS: selected_groups,
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(
        hass,
        entry,
    )

    assert entry.minor_version == 5
    assert CONF_SENSOR_GROUPS not in entry.data
    assert entry.options[CONF_SENSOR_GROUPS] == selected_groups


async def test_migrate_old_entry_adds_default_groups(
    hass: HomeAssistant,
) -> None:
    """Test migration of an old entry without sensor groups."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        data={
            "name": "Test",
            "latitude": 52.52,
            "longitude": 13.405,
            "grid_cell": (416, 784),
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(
        hass,
        entry,
    )

    assert entry.minor_version == 5
    assert CONF_SENSOR_GROUPS not in entry.data
    assert entry.options[CONF_SENSOR_GROUPS] == DEFAULT_SENSOR_GROUPS


async def test_migration_preserves_existing_options(
    hass: HomeAssistant,
) -> None:
    """Test that existing options take precedence during migration."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=4,
        data={
            "name": "Test",
            "latitude": 52.52,
            "longitude": 13.405,
            "grid_cell": (416, 784),
            CONF_SENSOR_GROUPS: [SENSOR_GROUP_CURRENT],
        },
        options={
            CONF_SENSOR_GROUPS: [SENSOR_GROUP_EVENT],
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(
        hass,
        entry,
    )

    assert entry.minor_version == 5
    assert CONF_SENSOR_GROUPS not in entry.data
    assert entry.options[CONF_SENSOR_GROUPS] == [SENSOR_GROUP_EVENT]


async def test_config_entry_setup_runs_migration(
    hass: HomeAssistant,
    mock_setup_entry,
) -> None:
    """Test Home Assistant migrates the entry before setup."""

    selected_groups = [
        SENSOR_GROUP_CURRENT,
        SENSOR_GROUP_EVENT,
    ]

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=4,
        title="Test",
        data={
            "name": "Test",
            "latitude": 52.52,
            "longitude": 13.405,
            "grid_cell": (416, 784),
            CONF_SENSOR_GROUPS: selected_groups,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(
        entry.entry_id,
    )

    await hass.async_block_till_done()

    assert entry.minor_version == 5

    assert CONF_SENSOR_GROUPS not in entry.data

    assert entry.options[
        CONF_SENSOR_GROUPS
    ] == selected_groups

    mock_setup_entry.assert_awaited_once_with(
        hass,
        entry,
    )

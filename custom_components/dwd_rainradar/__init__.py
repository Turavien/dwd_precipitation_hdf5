"""DWD Rain Radar integration."""

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import UpdateCoordinator
from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    PLATFORMS,
)
from .registry import (
    async_remove_disabled_entities,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MyData:
    """Runtime data definition."""

    coordinator: UpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up DWD Rain Radar from a config entry."""

    coordinator = UpdateCoordinator(
        hass,
        entry,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MyData(
        coordinator,
    )

    entry.async_on_unload(
        entry.add_update_listener(
            update_listener,
        )
    )

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate old config entries."""

    if entry.minor_version < 2:

        data = dict(entry.data)

        data.setdefault(
            CONF_SENSOR_GROUPS,
            DEFAULT_SENSOR_GROUPS,
        )

        hass.config_entries.async_update_entry(
            entry,
            data=data,
            minor_version=2,
        )

    return True


async def update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Handle config entry updates."""

    await async_remove_disabled_entities(
        hass,
        entry,
    )

    await hass.config_entries.async_reload(
        entry.entry_id,
    )


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the config entry."""

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

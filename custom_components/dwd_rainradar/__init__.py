"""DWD Rain Radar integration."""

# Derived in part from DWD Precipitation by Hoffmann77.
# Substantially modified for DWD Rain Radar by Turavien, 2026.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import UpdateCoordinator
from .engine import Engine
from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    PLATFORMS,
)
from .registry import (
    async_remove_disabled_entities,
)


@dataclass
class MyData:
    """Runtime data definition."""

    coordinator: UpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up DWD Rain Radar from a config entry."""

    await async_remove_disabled_entities(
        hass,
        entry,
    )

    domain_data = hass.data.setdefault(
        DOMAIN,
        {},
    )

    engine = domain_data.get(
        "engine",
    )

    if engine is None:
        engine = Engine(
            hass,
        )

        domain_data[
            "engine"
        ] = engine

    coordinator = UpdateCoordinator(
        hass,
        entry,
        engine,
    )

    setup_completed = False

    try:
        await coordinator.async_config_entry_first_refresh()

        setup_completed = True

    finally:
        if not setup_completed:
            coordinator.unregister_engine()

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

    data = dict(
        entry.data
    )

    options = dict(
        entry.options
    )

    if entry.minor_version < 2:

        data.setdefault(
            CONF_SENSOR_GROUPS,
            DEFAULT_SENSOR_GROUPS,
        )

    if entry.minor_version < 5:

        sensor_groups = data.pop(
            CONF_SENSOR_GROUPS,
            options.get(
                CONF_SENSOR_GROUPS,
                DEFAULT_SENSOR_GROUPS,
            ),
        )

        options.setdefault(
            CONF_SENSOR_GROUPS,
            sensor_groups,
        )

    hass.config_entries.async_update_entry(
        entry,
        data=data,
        options=options,
        unique_id=None,
        minor_version=5,
    )

    return True


async def update_listener(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Handle config entry updates."""

    await hass.config_entries.async_reload(
        entry.entry_id,
    )


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the config entry."""

    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if not unloaded:
        return False

    runtime_data: MyData = entry.runtime_data

    runtime_data.coordinator.unregister_engine()

    if not hass.config_entries.async_loaded_entries(
        DOMAIN,
    ):

        domain_data = hass.data.get(
            DOMAIN,
        )

        if domain_data is not None:

            engine = domain_data.get(
                "engine",
            )

            if isinstance(
                engine,
                Engine,
            ):
                await engine.async_shutdown()

        hass.data.pop(
            DOMAIN,
            None,
        )

    return True

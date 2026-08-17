"""Helpers for maintaining the entity registry."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
)
from .entity_groups import ENTITY_GROUPS

async def async_remove_disabled_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Remove entities no longer offered by this config entry."""

    registry = er.async_get(
        hass,
    )

    enabled_groups = set(
        entry.options.get(
            CONF_SENSOR_GROUPS,
            entry.data.get(
                CONF_SENSOR_GROUPS,
                DEFAULT_SENSOR_GROUPS,
            ),
        )
    )

    active_unique_ids = {
        f"{entry.entry_id}_{entity_key}"
        for group, entity_keys in ENTITY_GROUPS.items()
        if group in enabled_groups
        for entity_key in entity_keys
    }

    for entity in er.async_entries_for_config_entry(
        registry,
        entry.entry_id,
    ):
        if entity.unique_id in active_unique_ids:
            continue

        registry.async_remove(
            entity.entity_id,
        )

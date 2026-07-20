"""Helpers for maintaining the entity registry."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_SENSOR_GROUPS
from .entity_groups import ENTITY_GROUPS


async def async_remove_disabled_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Remove entities that belong to disabled sensor groups."""

    enabled_groups = set(
        entry.data.get(
            CONF_SENSOR_GROUPS,
            [],
        )
    )

    registry = er.async_get(
        hass,
    )

    for group, entity_keys in ENTITY_GROUPS.items():

        if group in enabled_groups:
            continue

        for entity_key in entity_keys:

            unique_id = (
                f"{entry.entry_id}_{entity_key}"
            )

            for platform in (
                "sensor",
                "binary_sensor",
            ):

                entity_id = registry.async_get_entity_id(
                    platform,
                    entry.domain,
                    unique_id,
                )

                if entity_id is None:
                    continue

                registry.async_remove(
                    entity_id,
                )

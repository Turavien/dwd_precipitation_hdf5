"""Binary sensor entities for DWD Rain Radar."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    SENSOR_GROUP_EVENT,
)
from .coordinator import UpdateCoordinator
from .entity import DwdRainRadarEntity
from .products import (
    Product,
    RV,
)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RainBinarySensorDescription(
    BinarySensorEntityDescription,
):
    """Binary sensor description."""

    product: Product
    sensor_group: str
    value_fn: Callable[
        [UpdateCoordinator],
        bool | None,
    ]


BINARY_SENSORS = (

    RainBinarySensorDescription(
        key="radvor_rv_active",
        product=RV,
        translation_key="precipitation_active",
        sensor_group=SENSOR_GROUP_EVENT,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_active,
    ),

)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""

    enabled_groups = set(
        entry.options.get(
            CONF_SENSOR_GROUPS,
            entry.data.get(
                CONF_SENSOR_GROUPS,
                DEFAULT_SENSOR_GROUPS,
            ),
        )
    )

    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        DwdRainRadarBinarySensor(
            coordinator,
            description,
        )
        for description in BINARY_SENSORS
        if description.sensor_group in enabled_groups
    )


class DwdRainRadarBinarySensor(
    DwdRainRadarEntity,
    BinarySensorEntity,
):
    """DWD Rain Radar binary sensor."""

    def __init__(
        self,
        coordinator: UpdateCoordinator,
        description: RainBinarySensorDescription,
    ) -> None:
        """Initialize the entity."""

        super().__init__(
            coordinator,
            description.key,
            description.product,
        )

        self.entity_description = description

    @property
    def is_on(
        self,
    ) -> bool | None:
        """Return whether precipitation is active."""

        if self.coordinator.data is None:
            return None

        return self.entity_description.value_fn(
            self.coordinator,
        )

"""Binary sensor entities for DWD Rain Radar."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .coordinator import UpdateCoordinator

from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    DOMAIN,
    SENSOR_GROUP_EVENT,
)


@dataclass(frozen=True, kw_only=True)
class RainBinarySensorDescription(
    BinarySensorEntityDescription,
):
    """Binary sensor description."""

    sensor_group: str
    value_fn: Callable[[dict], bool]


BINARY_SENSORS = (

    RainBinarySensorDescription(
        key="radvor_rv_active",
        translation_key="precipitation_active",
        sensor_group=SENSOR_GROUP_EVENT,
        value_fn=lambda data:
            data["rv"]["precipitation_active"]
            if data.get("rv")
            else False,
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
    CoordinatorEntity,
    BinarySensorEntity,
):
    """DWD Rain Radar binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UpdateCoordinator,
        description: RainBinarySensorDescription,
    ) -> None:

        super().__init__(coordinator)

        self.entity_description = description

        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_"
            f"{description.key}"
        )

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (
                    DOMAIN,
                    coordinator.config_entry.entry_id,
                )
            },
            name=(
                coordinator.config_entry.title
                or "DWD Rain Radar"
            ),
        )

    @property
    def is_on(self) -> bool:

        data = self.coordinator.data

        if data is None:
            return False

        return self.entity_description.value_fn(data)

"""Sensor entities for DWD precipitation data."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    DeviceInfo,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)

from .const import DOMAIN
from .coordinator import UpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class PrecipitationDescription(
    SensorEntityDescription,
):
    """Sensor description."""

    value_fn: Callable[[dict], float | None]


SENSORS = (

    PrecipitationDescription(
        key="radolan_rw",
        translation_key="precipitation_last_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data["rw"],
    ),

    PrecipitationDescription(
        key="radolan_sf",
        translation_key="precipitation_last_24h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data["sf"],
    ),

    PrecipitationDescription(
        key="radvor_rq_005",
        translation_key="precipitation_next_5min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][0]
            if data.get("rq") and len(data["rq"]) > 0
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_010",
        translation_key="precipitation_next_10min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][1]
            if data.get("rq") and len(data["rq"]) > 1
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_015",
        translation_key="precipitation_next_15min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][2]
            if data.get("rq") and len(data["rq"]) > 2
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_030",
        translation_key="precipitation_next_30min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][3]
            if data.get("rq") and len(data["rq"]) > 3
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_045",
        translation_key="precipitation_next_45min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][4]
            if data.get("rq") and len(data["rq"]) > 4
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_060",
        translation_key="precipitation_next_60min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][5]
            if data.get("rq") and len(data["rq"]) > 5
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_090",
        translation_key="precipitation_next_90min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][6]
            if data.get("rq") and len(data["rq"]) > 6
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rq_120",
        translation_key="precipitation_next_120min",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rq"][7]
            if data.get("rq") and len(data["rq"]) > 7
            else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""

    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        DwdPrecipitationSensor(
            coordinator,
            description
        )
        for description in SENSORS
    )


class DwdPrecipitationSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Precipitation sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UpdateCoordinator,
        description: PrecipitationDescription,
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
                or "DWD Precipitation"
            ),
        )

    @property
    def native_value(self):

        data = self.coordinator.data

        if data is None:
            return None

        value = self.entity_description.value_fn(data)

        if value is None:
            return None

        return round(value, 1)

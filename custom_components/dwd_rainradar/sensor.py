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
        key="radvor_rs_1h",
        translation_key="precipitation_next_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rs"][0]
            if data.get("rs") and len(data["rs"]) > 0
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rs_2h",
        translation_key="precipitation_next_2h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rs"][1]
            if data.get("rs") and len(data["rs"]) > 1
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rs_3h",
        translation_key="precipitation_next_3h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rs"][2]
            if data.get("rs") and len(data["rs"]) > 2
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_now",
        translation_key="rain_now",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rv"]["rain_now"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_5min",
        translation_key="rain_5",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rv"]["rain_5"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_10min",
        translation_key="rain_10",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rv"]["rain_10"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_15min",
        translation_key="rain_15",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rv"]["rain_15"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_start",
        translation_key="rain_start",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda data:
            data["rv"]["rain_start"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_end",
        translation_key="rain_end",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda data:
            data["rv"]["rain_end"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_duration",
        translation_key="rain_duration",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda data:
            data["rv"]["rain_duration"]
            if data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_max",
        translation_key="max_intensity",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data:
            data["rv"]["max_intensity"]
            if data.get("rv")
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
        DwdRainRadarSensor(
            coordinator,
            description
        )
        for description in SENSORS
    )


class DwdRainRadarSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """DWD Rain Radar sensor."""

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
                or "DWD Rain Radar"
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

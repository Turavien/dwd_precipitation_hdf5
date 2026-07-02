"""Sensor entities for DWD precipitation data."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.const import (
    UnitOfPrecipitationDepth,
)
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

from datetime import datetime

from .attributes import RainAttributes
from .const import DOMAIN
from .coordinator import UpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class PrecipitationDescription(
    SensorEntityDescription,
):
    """Sensor description."""

    value_fn: Callable[
        [UpdateCoordinator],
        float | datetime | None
    ]

    attributes_fn: Callable[
        [UpdateCoordinator],
        dict[str, object]
    ] | None = None


# ------------------------------------------------------------------
# Historical precipitation
# ------------------------------------------------------------------

HISTORY_SENSORS = (

    PrecipitationDescription(
        key="radolan_rw",
        translation_key="precipitation_last_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rw"],
        attributes_fn=RainAttributes.rw,
    ),

    PrecipitationDescription(
        key="radolan_rw_2h",
        translation_key="precipitation_last_2h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rw_2h"],
    ),

    PrecipitationDescription(
        key="radolan_rw_3h",
        translation_key="precipitation_last_3h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rw_3h"],
    ),

    PrecipitationDescription(
        key="radolan_rw_6h",
        translation_key="precipitation_last_6h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rw_6h"],
    ),

    PrecipitationDescription(
        key="radolan_rw_12h",
        translation_key="precipitation_last_12h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rw_12h"],
    ),

    PrecipitationDescription(
        key="radolan_sf",
        translation_key="precipitation_last_24h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["sf"],
    ),
)

# ------------------------------------------------------------------
# Forecast precipitation sums
# ------------------------------------------------------------------

FORECAST_SENSORS = (

    PrecipitationDescription(
        key="radvor_rs_1h",
        translation_key="precipitation_next_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rs"][0]
            if coordinator.data.get("rs")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rs_2h",
        translation_key="precipitation_next_2h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rs"][1]
            if coordinator.data.get("rs")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rs_3h",
        translation_key="precipitation_next_3h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rs"][2]
            if coordinator.data.get("rs")
            else None,
    ),

)

# ------------------------------------------------------------------
# Current / short-term precipitation intensity
# ------------------------------------------------------------------

CURRENT_INTENSITY_SENSORS = (

    PrecipitationDescription(
        key="radvor_rv_now",
        translation_key="intensity_now",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_now"]
            if coordinator.data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_5min",
        translation_key="intensity_in_5min",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_5"]
            if coordinator.data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_10min",
        translation_key="intensity_in_10min",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_10"]
            if coordinator.data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_15min",
        translation_key="intensity_in_15min",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_15"]
            if coordinator.data.get("rv")
            else None,
    ),

)

# ------------------------------------------------------------------
# Next precipitation event
# ------------------------------------------------------------------

EVENT_SENSORS = (

    PrecipitationDescription(
        key="radvor_rv_start",
        translation_key="precipitation_start",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_start"]
            if coordinator.data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_duration",
        translation_key="precipitation_duration",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["precipitation_duration"]
            if coordinator.data.get("rv")
            else None,
    ),

)

# ------------------------------------------------------------------
# Forecast maximum precipitation intensity
# ------------------------------------------------------------------

FORECAST_INTENSITY_SENSORS = (

    PrecipitationDescription(
        key="radvor_rv_max",
        translation_key="max_intensity",
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["max_intensity"]
            if coordinator.data.get("rv")
            else None,
    ),

    PrecipitationDescription(
        key="radvor_rv_max_at",
        translation_key="max_intensity_at",
        native_unit_of_measurement="min",
        suggested_display_precision=0,
        value_fn=lambda coordinator:
            coordinator.data["rv"]["max_intensity_at"]
            if coordinator.data.get("rv")
            else None,
    ),

)

SENSORS = (
    *CURRENT_INTENSITY_SENSORS,
    *FORECAST_INTENSITY_SENSORS,
    *EVENT_SENSORS,
    *FORECAST_SENSORS,
    *HISTORY_SENSORS,
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

        if self.coordinator.data is None:
            return None

        value = self.entity_description.value_fn(
            self.coordinator
        )

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            return round(value, 1)

        return value

    @property
    def extra_state_attributes(self):

        if (
            self.entity_description.attributes_fn
            is None
        ):
            return None

        return self.entity_description.attributes_fn(
            self.coordinator
        )

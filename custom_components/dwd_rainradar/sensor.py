"""Sensor entities for DWD precipitation data."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfTime,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_SENSOR_GROUPS,
    DEFAULT_SENSOR_GROUPS,
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
    SENSOR_GROUP_FORECAST,
    SENSOR_GROUP_HISTORY,
    SENSOR_GROUP_ROLLING,
)
from .coordinator import UpdateCoordinator
from .entity import DwdRainRadarEntity
from .products import (
    Product,
    RS,
    RV,
    RW,
)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PrecipitationDescription(
    SensorEntityDescription,
):
    """Sensor description."""

    product: Product

    value_fn: Callable[
        [UpdateCoordinator],
        float | datetime | None
    ]

    attributes_fn: Callable[
        [UpdateCoordinator],
        dict[str, object]
    ] | None = None


def _rw_attributes(
    coordinator: UpdateCoordinator,
) -> dict[str, object]:
    """Return attributes for the native RW product."""

    rw = coordinator.data.rw

    return {
        "product": "RW",
        "source": "RADOLAN",
        "latest_measurement": (
            rw[-1].valid_until
            if rw
            else None
        ),
    }


# ------------------------------------------------------------------
# Historical precipitation
# ------------------------------------------------------------------

HISTORY_SENSORS = (

    PrecipitationDescription(
        key="radolan_rw",
        product=RW,
        translation_key="precipitation_last_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_1h,
        attributes_fn=_rw_attributes,
    ),

)

# ------------------------------------------------------------------
# Rolling historical precipitation
# ------------------------------------------------------------------

ROLLING_SENSORS = (

    PrecipitationDescription(
        key="radolan_rw_2h",
        product=RW,
        translation_key="precipitation_last_2h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_2h,
    ),

    PrecipitationDescription(
        key="radolan_rw_3h",
        product=RW,
        translation_key="precipitation_last_3h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_3h,
    ),

    PrecipitationDescription(
        key="radolan_rw_6h",
        product=RW,
        translation_key="precipitation_last_6h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_6h,
    ),

    PrecipitationDescription(
        key="radolan_rw_9h",
        product=RW,
        translation_key="precipitation_last_9h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_9h,
    ),

    PrecipitationDescription(
        key="radolan_rw_12h",
        product=RW,
        translation_key="precipitation_last_12h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_12h,
    ),

    PrecipitationDescription(
        key="radolan_rw_24h",
        product=RW,
        translation_key="precipitation_last_24h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_24h,
    ),

    PrecipitationDescription(
        key="radolan_rw_36h",
        product=RW,
        translation_key="precipitation_last_36h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_36h,
    ),

    PrecipitationDescription(
        key="radolan_rw_48h",
        product=RW,
        translation_key="precipitation_last_48h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=1,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_last_48h,
    ),

)

# ------------------------------------------------------------------
# Forecast precipitation sums
# ------------------------------------------------------------------

FORECAST_SENSORS = (

    PrecipitationDescription(
        key="radvor_rs_1h",
        product=RS,
        translation_key="precipitation_next_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_next_1h,
    ),

    PrecipitationDescription(
        key="radvor_rs_2h",
        product=RS,
        translation_key="precipitation_next_2h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_next_2h,
    ),

)

# ------------------------------------------------------------------
# Precipitation intensity
# ------------------------------------------------------------------

INTENSITY_SENSORS = (

    PrecipitationDescription(
        key="radvor_rv_now",
        product=RV,
        translation_key="intensity_now",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.intensity_now,
    ),

    PrecipitationDescription(
        key="radvor_rv_5min",
        product=RV,
        translation_key="intensity_in_5min",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.intensity_in_5min,
    ),

    PrecipitationDescription(
        key="radvor_rv_10min",
        product=RV,
        translation_key="intensity_in_10min",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.intensity_in_10min,
    ),

    PrecipitationDescription(
        key="radvor_rv_15min",
        product=RV,
        translation_key="intensity_in_15min",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.intensity_in_15min,
    ),

    PrecipitationDescription(
        key="radvor_rv_max",
        product=RV,
        translation_key="maximum_precipitation_intensity",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        suggested_display_precision=2,
        value_fn=lambda coordinator:
            coordinator.data.maximum_precipitation_intensity,
    ),

)

# ------------------------------------------------------------------
# Next precipitation event
# ------------------------------------------------------------------

EVENT_SENSORS = (

    PrecipitationDescription(
        key="radvor_rv_start",
        product=RV,
        translation_key="precipitation_start",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=0,
        value_fn=lambda coordinator:
            coordinator.data.precipitation_start,
    ),

)

SENSOR_GROUP_MAP = {
    SENSOR_GROUP_CURRENT: INTENSITY_SENSORS,
    SENSOR_GROUP_FORECAST: FORECAST_SENSORS,
    SENSOR_GROUP_EVENT: EVENT_SENSORS,
    SENSOR_GROUP_HISTORY: HISTORY_SENSORS,
    SENSOR_GROUP_ROLLING: ROLLING_SENSORS,
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""

    coordinator = entry.runtime_data.coordinator

    enabled_groups = entry.options.get(
        CONF_SENSOR_GROUPS,
        entry.data.get(
            CONF_SENSOR_GROUPS,
            DEFAULT_SENSOR_GROUPS,
        ),
    )

    descriptions = [
        description
        for group in enabled_groups
        for description in SENSOR_GROUP_MAP.get(
            group,
            (),
        )
    ]

    async_add_entities(
        DwdRainRadarSensor(
            coordinator,
            description,
        )
        for description in descriptions
    )


class DwdRainRadarSensor(
    DwdRainRadarEntity,
    SensorEntity,
):
    """DWD Rain Radar sensor."""

    def __init__(
        self,
        coordinator: UpdateCoordinator,
        description: PrecipitationDescription,
    ) -> None:
        """Initialize the entity."""

        super().__init__(
            coordinator,
            description.key,
            description.product,
        )

        self.entity_description = description

    @property
    def native_value(
        self,
    ) -> float | datetime | None:
        """Return the native sensor value."""

        if self.coordinator.data is None:
            return None

        return self.entity_description.value_fn(
            self.coordinator
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, object] | None:
        """Return additional state attributes."""

        if (
            self.coordinator.data is None
            or self.entity_description.attributes_fn
            is None
        ):
            return None

        return self.entity_description.attributes_fn(
            self.coordinator
        )

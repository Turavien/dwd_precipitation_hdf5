"""Entity groups for DWD Rain Radar."""

from .const import (
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_EVENT,
    SENSOR_GROUP_FORECAST,
    SENSOR_GROUP_HISTORY,
    SENSOR_GROUP_ROLLING,
)

ENTITY_GROUPS = {
    SENSOR_GROUP_CURRENT: (
        "radvor_rv_now",
        "radvor_rv_5min",
        "radvor_rv_10min",
        "radvor_rv_15min",
    ),

    SENSOR_GROUP_FORECAST: (
        "radvor_rs_1h",
        "radvor_rs_2h",
        "radvor_rs_3h",
    ),

    SENSOR_GROUP_EVENT: (
        "radvor_rv_start",
        "radvor_rv_max",
        "radvor_rv_active",
    ),

    SENSOR_GROUP_HISTORY: (
        "radolan_rw",
        "radolan_sf",
    ),

    SENSOR_GROUP_ROLLING: (
        "radolan_rw_2h",
        "radolan_rw_3h",
        "radolan_rw_6h",
        "radolan_rw_12h",
        "radolan_sf_36h",
        "radolan_sf_48h",
        "radolan_sf_72h",
    ),
}

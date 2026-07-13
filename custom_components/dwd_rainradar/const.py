"""Constants for DWD Rain Radar."""

from homeassistant.const import Platform


DOMAIN = "dwd_rainradar"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONF_COORDS = "coordinates"

CONF_SENSOR_GROUPS = "sensor_groups"

SENSOR_GROUP_CURRENT = "current"
SENSOR_GROUP_FORECAST = "forecast"
SENSOR_GROUP_EVENT = "event"
SENSOR_GROUP_HISTORY = "history"
SENSOR_GROUP_ROLLING = "rolling"

DEFAULT_SENSOR_GROUPS = [
    SENSOR_GROUP_CURRENT,
    SENSOR_GROUP_FORECAST,
    SENSOR_GROUP_EVENT,
    SENSOR_GROUP_HISTORY,
    SENSOR_GROUP_ROLLING,
]

DWD_OPENDATA_URL = (
    "https://opendata.dwd.de"
)

DWD_RADOLAN_URL = (
    f"{DWD_OPENDATA_URL}/weather/radar/radolan"
)

DWD_RADVOR_URL = (
    f"{DWD_OPENDATA_URL}/weather/radar/composite"
)

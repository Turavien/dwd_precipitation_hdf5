"""Constants for DWD Rain Radar."""

from homeassistant.const import Platform


DOMAIN = "dwd_rainradar"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONF_COORDS = "coordinates"

DWD_OPENDATA_URL = (
    "https://opendata.dwd.de"
)

DWD_RADOLAN_URL = (
    f"{DWD_OPENDATA_URL}/weather/radar/radolan"
)

DWD_RADVOR_URL = (
    f"{DWD_OPENDATA_URL}/weather/radar/composite"
)

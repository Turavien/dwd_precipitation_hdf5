# DWD Rain Radar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_rainradar)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_rainradar)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_rainradar)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_rainradar)

🇩🇪 Deutsche Version: [README.de.md](README.de.md)

> **Note**
>
> This is not an official integration of the German Weather Service (_Deutscher Wetterdienst_, DWD).
>
> This project is developed independently and is not affiliated with the DWD.
>
> It uses publicly available DWD Open Data products only.

This custom Home Assistant integration provides high-resolution radar and precipitation data from the German Weather Service (_Deutscher Wetterdienst_, DWD).

It combines historical precipitation analyses (RADOLAN) with short-term precipitation forecasts (RADVOR) and provides sensors optimized for Home Assistant automations.

Typical use cases include:

* automated garden irrigation
* rain warnings for open windows
* weather-based home automations

> **Important**
>
> The forecast sensors provide the expected precipitation totals for the next
>
> * 1 hour
> * 2 hours
> * 3 hours
>
> Each value represents the total amount of precipitation expected to fall during the corresponding forecast period.

## How it works

The integration is based on official DWD radar products.

The radar grids provide a spatial resolution of approximately 1 km × 1 km and consist of 1100 × 1200 grid cells.

For the configured location, the grid cell whose center point is closest to the configured coordinates is selected automatically.

The integration uses:

* RADOLAN RW
* RADOLAN SF
* RADVOR RS
* RADVOR RV

and provides:

* Total precipitation during the last hour [mm]
* Total precipitation during the last 24 hours [mm]

* Expected precipitation during the next hour [mm]
* Expected precipitation during the next 2 hours [mm]
* Expected precipitation during the next 3 hours [mm]

* Current precipitation intensity [mm/h]
* Expected precipitation intensity in 5 minutes [mm/h]
* Expected precipitation intensity in 10 minutes [mm/h]
* Expected precipitation intensity in 15 minutes [mm/h]
* Start of the next precipitation event [min]
* End of the next precipitation event [min]
* Duration of the next precipitation event [min]
* Maximum precipitation intensity during the next precipitation event [mm/h]
* Binary sensor "Rain active"

## Special features

The integration combines several official radar products provided by the German Weather Service (_Deutscher Wetterdienst_, DWD).

Depending on the sensor, it provides either

* measured precipitation totals,
* forecast precipitation totals, or
* precipitation intensities.

Forecast totals are based on the RADVOR RS product and provide the expected precipitation for the next one to three hours.

Precipitation intensities are based on the RADVOR RV product and additionally allow the detection of continuous precipitation events.

The following event-based sensors are derived from these data:

* Rain active
* Rain starts
* Rain ends
* Rain duration
* Maximum precipitation intensity during the precipitation event

This makes the integration suitable for both automated irrigation systems and time-critical weather-based automations such as open-window rain warnings.

The integration only works within Germany and nearby border regions covered by DWD radar products.

Locations outside the supported DWD radar coverage area are rejected during configuration.

## Data Sources

All data is provided by the German Weather Service (_Deutscher Wetterdienst_, DWD).

### RADVOR RS

Radar-based forecast of accumulated precipitation totals for one-hour forecast periods.

### RADVOR RV

Radar-based forecast of precipitation intensity with a five-minute temporal resolution.

### RADOLAN RW

Radar-based precipitation analysis for the last hour.

### RADOLAN SF

Radar-based precipitation analysis for the last 24 hours.

## Installation via HACS

1. Open HACS
2. Add a custom repository
3. Enter the repository URL
4. Select category “Integration”
5. Install the integration
6. Restart Home Assistant

## Project History

This project originally started as a continuation of the [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) integration by [@Hoffmann77](https://github.com/Hoffmann77).

After the German Weather Service (_Deutscher Wetterdienst_, DWD) migrated its radar products to HDF5, the original integration was first adapted and later evolved into an independent project.

While the original concept remains the foundation, the architecture, data processing and feature set have since been extensively redesigned and expanded.

## License and Credits

Parts of the radar processing are based on components of the wradlib project.
The wradlib license can be found under:
custom_components/dwd_rainradar/radar/LICENSE.txt

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

This custom Home Assistant integration provides high-resolution radar-based precipitation data from the German Weather Service (_Deutscher Wetterdienst_, DWD).

It combines measured precipitation analyses (RADOLAN) with short-term radar forecasts (RADVOR) and exposes the data as Home Assistant entities.

Typical use cases include:

* automated garden irrigation
* rain warnings for open windows
* weather-based home automations
* weather-dependent control of shutters, awnings and outdoor devices

The integration is fully configurable through Home Assistant's user interface. During setup you can select which groups of sensors should be created. Sensor groups can be enabled or disabled later at any time via the integration options without removing and re-adding the integration.

> **Important**
>
> Forecast sensors report the **expected accumulated precipitation** for the upcoming
>
> * 1 hour
> * 2 hours
> * 3 hours
>
> Each value represents the total precipitation expected to fall during the corresponding forecast period. They are **not** instantaneous precipitation intensities.

## Features

* High-resolution radar-based precipitation data provided by the German Weather Service (DWD)
* Combination of measured precipitation analyses (RADOLAN) and short-term radar forecasts (RADVOR)
* Automatic selection of the nearest radar grid cell for the configured location
* Optional sensor groups
* Fully configurable through Home Assistant ConfigFlow and OptionsFlow
* Rolling precipitation totals calculated from official DWD data
* Home Assistant entities for measured, forecast and derived precipitation data
* Automatic cleanup of entities that belong to disabled sensor groups
* English and German translations

## How it works

The integration is based exclusively on official radar products published by the German Weather Service (_Deutscher Wetterdienst_, DWD).

Radar data is provided as a grid with a spatial resolution of approximately **1 km × 1 km** and a size of **1100 × 1200** grid cells.

During setup, the integration automatically determines the radar grid cell whose center is closest to the configured location. All sensors are calculated from the data of this grid cell. This ensures spatial consistency across all measured, forecast and calculated entities.

The integration currently uses the following DWD products:

* RADOLAN RW
* RADOLAN SF
* RADVOR RS
* RADVOR RV

It provides the following entities:

### Historical precipitation

* Total precipitation during the last hour [mm]
* Calculated rolling precipitation during the last 2 hours [mm]
* Calculated rolling precipitation during the last 3 hours [mm]
* Calculated rolling precipitation during the last 6 hours [mm]
* Calculated rolling precipitation during the last 12 hours [mm]
* Total precipitation during the last 24 hours [mm]

### Forecast precipitation

* Expected precipitation during the next hour [mm]
* Expected precipitation during the next 2 hours [mm]
* Expected precipitation during the next 3 hours [mm]

### Current precipitation

* Current precipitation intensity [mm/h]
* Expected precipitation intensity in 5 minutes [mm/h]
* Expected precipitation intensity in 10 minutes [mm/h]
* Expected precipitation intensity in 15 minutes [mm/h]
* Precipitation active (binary sensor)

### Rain event

* Time until next precipitation [min]

## Characteristics

The integration combines multiple official DWD radar products into a single data model.

Depending on the entity, the integration provides:

* measured precipitation totals (RADOLAN)
* forecast precipitation totals (RADVOR RS)
* forecast precipitation intensities (RADVOR RV)
* calculated rolling precipitation totals derived from official DWD measurements

All entities are created from the same radar grid cell, ensuring that measured values, forecasts and calculated entities always refer to exactly the same location.

Sensor groups can be enabled or disabled individually during setup and later via the integration options. Only the selected sensor groups are created.

Typical applications include:

* automated irrigation
* rain warnings for open windows
* protection of awnings and shutters
* weather-dependent control of outdoor devices

The integration is available only within Germany and nearby border regions covered by the official DWD radar products. Locations outside the supported radar coverage are rejected during configuration.

## Data Sources

All data is obtained from publicly available Open Data products published by the German Weather Service (_Deutscher Wetterdienst_, DWD).

The integration currently uses four official radar products, each serving a different purpose.

### RADOLAN RW

Hourly radar-based precipitation analysis.

This product provides the measured precipitation total for the last hour and serves as the basis for the calculated rolling precipitation totals (2 h, 3 h, 6 h and 12 h).

### RADOLAN SF

Radar-based precipitation analysis for the previous 24 hours.

This product provides the measured precipitation total during the last 24 hours.

### RADVOR RS

Radar-based forecast of accumulated precipitation.

It provides the expected accumulated precipitation during the next:

* 1 hour
* 2 hours
* 3 hours

### RADVOR RV

Radar-based precipitation intensity forecast with a temporal resolution of five minutes.

This product is used to derive:

* current precipitation intensity
* forecast precipitation intensity after 5 minutes
* forecast precipitation intensity after 10 minutes
* forecast precipitation intensity after 15 minutes
* the calculated precipitation event start
* the binary sensor **Precipitation active**

## Installation via HACS

1. Open **HACS**.
2. Add this repository as a **Custom Repository**.
3. Select the category **Integration**.
4. Install **DWD Rain Radar**.
5. Restart Home Assistant.

After the restart:

1. Go to **Settings → Devices & Services**.
2. Click **Add Integration**.
3. Search for **DWD Rain Radar**.
4. Enter or select the desired location.
5. Select the sensor groups you want to create.
6. Finish the configuration.

Sensor groups can be changed later at any time via **Settings → Devices & Services → DWD Rain Radar → Configure** without removing and re-adding the integration.

## Project History

DWD Rain Radar originated as a continuation of the [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) integration created by [@Hoffmann77](https://github.com/Hoffmann77).

When the German Weather Service (_Deutscher Wetterdienst_, DWD) migrated its radar products to the HDF5 format, the original integration required substantial changes. This project initially focused on restoring compatibility before gradually evolving into an independent integration.

Today, DWD Rain Radar has its own architecture, configuration flow, sensor model and development roadmap while continuing to build upon the ideas of the original project.

## License and Credits

This project is released under the MIT License.

Parts of the radar processing are based on components of the **wradlib** project.

The corresponding license is included in this repository:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback and Contributions

Bug reports, feature requests and pull requests may be submitted through GitHub.

Issues and feature requests can be reported through the GitHub issue tracker.

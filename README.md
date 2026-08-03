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

This custom Home Assistant integration brings official radar-based precipitation products from the German Weather Service (_Deutscher Wetterdienst_, DWD) into Home Assistant.

It combines RADOLAN measurements with RADVOR forecasts to provide measured, forecast and derived precipitation entities for a single radar grid cell.

Typical applications include:

* automated garden irrigation
* rain warnings for open windows
* weather-dependent home automations
* control of shutters, awnings and outdoor devices

The integration is fully configurable through the Home Assistant user interface. Sensor groups can be selected during setup and changed later at any time through the integration options.

> **Important**
>
> Forecast sensors report the **expected accumulated precipitation** for the upcoming
>
> * 1 hour
> * 2 hours
>
> Each value represents the total precipitation expected to fall during the corresponding forecast period. They are **not** instantaneous precipitation intensities.

## Screenshots

### Integration

![Integration](images/en/integration.png)

### Options

![Options](images/en/options.png)

### Entities

![Entities](images/en/entities.png)

## Features

* Official DWD radar products (RADOLAN & RADVOR)
* Measured, forecast and derived precipitation entities
* Automatic radar grid selection for the configured location
* Optional sensor groups
* Rolling precipitation totals up to 48 hours
* Full ConfigFlow and OptionsFlow support
* Automatic cleanup of disabled entities
* English and German translations

## How it works

The integration exclusively uses official DWD radar products.

Radar data is published on a grid of approximately **1 km × 1 km**. During setup, the nearest grid cell is selected automatically, and all entities are derived from this single location.

The integration uses the following DWD products:

* RADOLAN RW
* RADVOR RS
* RADVOR RV

It provides the following entities:

### Historical precipitation

* Total precipitation during the last hour [mm]
* Total precipitation during the last 2 hours [mm]
* Total precipitation during the last 3 hours [mm]
* Total precipitation during the last 6 hours [mm]
* Total precipitation during the last 9 hours [mm]
* Total precipitation during the last 12 hours [mm]
* Total precipitation during the last 24 hours [mm]
* Total precipitation during the last 36 hours [mm]
* Total precipitation during the last 48 hours [mm]

### Forecast precipitation

* Expected precipitation during the next hour [mm]
* Expected precipitation during the next 2 hours [mm]

### Current precipitation

* Current precipitation intensity [mm/h]
* Expected precipitation intensity in 5 minutes [mm/h]
* Expected precipitation intensity in 10 minutes [mm/h]
* Expected precipitation intensity in 15 minutes [mm/h]

### Rain event

* Time until next precipitation [min]
* Expected max. precipitation intensity next 2 hours [mm/h]
* Precipitation active (binary sensor)

This sensor group combines information about the next expected precipitation together with the highest forecast precipitation intensity within the three-hour RADVOR forecast period.

## Data Sources

The integration currently uses three official DWD Open Data radar products, each serving a specific purpose.

### RADOLAN RW

Radar-based precipitation total of the previous hour.

The integration stores consecutive hourly RW products locally and derives all historical precipitation totals from this history (1 h, 2 h, 3 h, 6 h, 9 h, 12 h, 24 h, 36 h and 48 h).

### RADVOR RS

Radar-based accumulated precipitation forecast covering the next 120 minutes with a temporal resolution of five minutes.

This product provides the forecast precipitation totals for the next 1 and 2 hours.

### RADVOR RV

Radar-based precipitation intensity forecast covering the next 120 minutes with a temporal resolution of five minutes.

This product provides the current and forecast precipitation intensities and is used to derive the binary sensor **Precipitation active** and the time until the next precipitation.

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

## Project History

DWD Rain Radar originated as a continuation of the [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) integration created by [@Hoffmann77](https://github.com/Hoffmann77).

When the German Weather Service (_Deutscher Wetterdienst_, DWD) migrated its radar products to HDF5, the original integration required substantial changes. This project started as a compatibility update and has since evolved into an independent integration with its own architecture, configuration flow and sensor model.

## License and Credits

This project is released under the MIT License.

Parts of the radar processing are based on components of the **wradlib** project.

The corresponding license is included in this repository:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback and Contributions

Bug reports, feature requests and pull requests are welcome through the GitHub repository.

# DWD Rain Radar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_precipitation_hdf5)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_precipitation_hdf5)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_precipitation_hdf5)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_precipitation_hdf5)

🇩🇪 Deutsche Version: [README.de.md](README.de.md)

# DWD Rain Radar

> **Note**
>
> This is not an official integration of the German weather service _Deutscher Wetterdienst_ (DWD).
>
> This project is developed independently and is not affiliated with the Deutscher Wetterdienst.
>
> It uses publicly available DWD Open Data products only.

This custom Home Assistant integration provides high-resolution precipitation data from the _Deutscher Wetterdienst_ (DWD).

The project originated as a continuation of the [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) integration by [@Hoffmann77](https://github.com/Hoffmann77) after the DWD migrated its data products to HDF5, which temporarily rendered the original integration unusable.

During this transition, most of the code was reworked and the provided entities were adapted to better suit individual use cases, especially automated garden irrigation control.

## How it works

The integration is based on official DWD radar products.

The radar grids provide a spatial resolution of approximately 1 km × 1 km and consist of 1100 × 1200 grid cells.

For the configured location, the grid cell whose center point is closest to the configured coordinates is selected automatically.

The integration uses:

* RADOLAN RW
* RADOLAN SF
* RADVOR RQ

and provides:

* Total precipitation during the last hour [mm]
* Total precipitation during the last 24 hours [mm]
* Cumulative precipitation forecasts [mm]

  * within the next 5 minutes
  * within the next 10 minutes
  * within the next 15 minutes
  * within the next 30 minutes
  * within the next 45 minutes
  * within the next 60 minutes
  * within the next 90 minutes
  * within the next 120 minutes

## Special features

Forecast values are internally calculated by accumulating all available five-minute RADVOR forecast intervals.

As a result, the integration provides the actually expected precipitation totals in millimetres [mm] rather than instantaneous precipitation intensities [mm/h].

The integration only works within Germany and nearby border regions covered by DWD radar products.

Locations outside the supported DWD radar coverage area are rejected during configuration.

## Data Sources

All data is provided by the German Weather Service (DWD).

### RADVOR RQ

Radar-based short-term precipitation forecasts with high temporal and spatial resolution.

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

## License and Credits

The original integration was published by [@Hoffmann77](https://github.com/Hoffmann77).
This version has been extensively reworked and adapted to the current structure of the DWD RADVOR forecast data.

Parts of the radar processing are based on components of the wradlib project.
The wradlib license can be found under:
custom_components/dwd_precipitation_hdf5/radar/LICENSE.txt

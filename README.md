# DWD Precipitation HDF5

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_precipitation_hdf5)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_precipitation_hdf5)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_precipitation_hdf5)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_precipitation_hdf5)

🇩🇪 Deutsche Version: [README.de.md](README.de.md)

This custom Home Assistant integration provides high-resolution precipitation data from the German Weather Service (DWD).

The data is based on radar composites with an approximate spatial resolution of 1 km × 1 km.

The integration automatically selects the nearest radar grid cell for the configured location.

The integration uses:

* RADOLAN RW
* RADOLAN SF
* RADVOR RQ

and provides:

* precipitation during the last hour [mm]
* precipitation during the last 24 hours [mm]
* cumulative precipitation forecasts [mm] for:

  * +5 minutes
  * +10 minutes
  * +15 minutes
  * +30 minutes
  * +45 minutes
  * +60 minutes
  * +90 minutes
  * +120 minutes

## Special Features

Forecast values are internally calculated by cumulatively processing all available 5-minute RADVOR forecast intervals.

The integration therefore provides actual precipitation sums in millimeters [mm] instead of instantaneous precipitation intensities [mm/h].

The integration only works within Germany and nearby border regions where DWD radar data is available.

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

The original integration was published by @Hoffmann77.

This version has been extensively reworked and adapted to the current structure of the DWD RADVOR forecast data.

Parts of the radar processing are based on components of the wradlib project.

The wradlib license can be found under:

custom_components/dwd_precipitation_hdf5/radar/LICENSE.txt

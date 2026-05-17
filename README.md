# DWD Precipitation HDF5

Custom Home Assistant integration providing high-resolution precipitation
analysis and short-term precipitation forecasts for Germany based on
DWD RADOLAN and RADVOR data.

This integration provides:

- precipitation [mm] during the last hour
- precipitation [mm] during the last 24 hours
- cumulative precipitation forecasts [mm] within:
  - next 5 minutes
  - next 10 minutes
  - next 15 minutes
  - next 30 minutes
  - next 45 minutes
  - next 60 minutes
  - next 90 minutes
  - next 120 minutes

Forecast values are internally calculated from all available 5-minute
RADVOR forecast intervals and accumulated into cumulative precipitation
totals for the selected time windows.

The integration supports locations within Germany and nearby border
regions covered by the RADOLAN/RADVOR grid.

---

# Data sources

All weather data is provided by the Deutscher Wetterdienst (DWD).

Used products:

- RADVOR RQ
- RADOLAN RW
- RADOLAN SF

More information:

https://www.dwd.de

---

# Installation

## HACS

Add this repository as a custom repository in HACS.

Category:
Integration

Restart Home Assistant after installation.

Then add the integration via:

Settings
→ Devices & Services
→ Add Integration

---

## Manual installation

Copy:

custom_components/dwd_precipitation_hdf5

into your Home Assistant configuration directory.

Restart Home Assistant afterwards.

---

# Disclaimer

This is an independent custom Home Assistant integration.

It is not affiliated with, endorsed by, or connected to
Deutscher Wetterdienst (DWD).

Weather forecasts and precipitation estimations may contain inaccuracies
and should not be used for safety-critical decisions.

---

# Origin

Originally based on work by @Hoffmann77.

This version has been extensively modified and extended, including:

- migration to HDF5 processing
- cumulative precipitation calculations
- localization support
- improved fallback handling
- additional forecast intervals
- Home Assistant compatibility fixes

---

# License

This project includes adapted components derived from wradlib.

The wradlib license can be found under:

radar/LICENSE.txt

The integration itself is licensed under the MIT License.

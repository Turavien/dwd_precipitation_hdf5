# DWD Rain Radar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_rainradar)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_rainradar)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.3%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)

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

The integration is fully configurable through the Home Assistant user interface.

## Configuration

### Initial setup

The following information is requested during initial setup:

* **Name** – display name of the location in Home Assistant.
* **Location** – latitude and longitude of the location to evaluate. The location can be selected with the Home Assistant location selector. The integration automatically determines the corresponding DWD radar grid cell.
* **Sensor groups** – determines which entities are created for this location.

The following sensor groups are available:

* **Intensities** – current intensity, +5, +10 and +15 minutes and the maximum expected intensity during the next two hours.
* **Forecast totals** – expected precipitation totals during the next one and two hours.
* **Precipitation event** – precipitation active and time until the next expected precipitation.
* **Last 1 hour total** – latest RADOLAN RW hourly precipitation total.
* **Rolling totals** – precipitation totals during the previous 2 to 48 hours.

### Options

The enabled sensor groups can be changed at any time through the integration options. Entities belonging to groups that are no longer selected are automatically removed from the entity registry.

### Reconfigure

The **Reconfigure** flow can be used to change the name and location of an existing entry without removing and setting up the integration again.

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
* Setup and options entirely through the Home Assistant user interface
* Automatic cleanup of entities no longer provided
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

### Precipitation intensity

* Current precipitation intensity [mm/h]
* Expected precipitation intensity in 5 minutes [mm/h]
* Expected precipitation intensity in 10 minutes [mm/h]
* Expected precipitation intensity in 15 minutes [mm/h]
* Maximum expected precipitation intensity during the next 2 hours [mm/h]

### Precipitation event

* Time until next expected precipitation [min]
* Precipitation active (binary sensor)

## Data Sources

Data source: Deutscher Wetterdienst (DWD) Open Data. The values exposed by this integration are processed and derived from these source products.

The integration currently uses three official DWD Open Data radar products, each serving a specific purpose.

### RADOLAN RW

Gauge-adjusted radar-based precipitation total over one hour.

RW is published for overlapping time windows. The integration keeps the required RW history locally and selects a continuous sequence of non-overlapping hourly intervals for each calculation. This provides precipitation totals for 1 h, 2 h, 3 h, 6 h, 9 h, 12 h, 24 h, 36 h and 48 h.

### RADVOR RS

Radar-based one-hour precipitation forecast provided every five minutes for different forecast times.

For the next one and two hour sensors, the integration uses the first one or two non-overlapping 60-minute forecast intervals of the latest DWD run. These intervals are anchored to the DWD analysis time. Because the product becomes available with a delay, they therefore do not exactly represent a 60- or 120-minute period shifted from the current wall-clock time. The integration deliberately does not interpolate precipitation within an hourly interval.

### RADVOR RV

Radar-based precipitation forecast in five-minute intervals covering the next 120 minutes.

For the current intensity, the integration uses the RV five-minute interval containing the actual current time. Forecasts in 5, 10 and 15 minutes use the intervals containing the real current time plus 5, 10 and 15 minutes respectively. This means these sensors continue to advance with real time even between two DWD publications. The precipitation amount of each interval is converted to an equivalent intensity in mm/h. These values also provide the binary sensor **Precipitation active**, the real time until precipitation is next expected and the maximum expected intensity within the remaining available RV forecast horizon.

## Data freshness and availability

The integration evaluates RW, RS and RV freshness independently. A product remains current until its next expected publication time, including the known publication delay and an additional five-minute grace period. With the DWD timing parameters currently used by the integration, this corresponds to about 39 minutes for RW and 13 minutes for RS and RV, measured from the timestamp of the latest received product.

If only one product remains unchanged beyond that point, only the entities depending on that product are marked **unavailable**. Other sensor groups remain usable as long as their own DWD product is current. The affected entities automatically become available again as soon as a newer product arrives. A complete connection failure to DWD continues to be handled centrally by the Home Assistant update coordinator.

## Diagnostics

Home Assistant can generate diagnostic data for each integration entry. Diagnostics can be downloaded from the integration entry menu under **Settings → Devices & Services → DWD Rain Radar** and can be attached to issue reports.

The diagnostics include, among other information:

* Home Assistant update coordinator status
* timestamps and freshness status of RW, RS and RV
* publication and freshness timing of the DWD products
* public HTTP metadata such as ETag and Last-Modified
* number of registered grid cells and config-entry references
* internal state and rolling-cache status
* status of running RW backfill tasks

For privacy reasons, **no location information** is included. In particular, the diagnostics do not contain the configured name, latitude, longitude or the actual DWD grid cell of the configured location.

## Data updates

The Home Assistant update coordinator runs every **30 seconds**. This does not mean that product files are downloaded from DWD every 30 seconds.

The integration is aware of the publication schedule of each DWD product and performs a remote request only when a newer product can reasonably be expected.

The following timing parameters are currently used:

* **RADVOR RV** – a new product timestamp every 5 minutes with an expected publication delay of about 3 minutes.
* **RADVOR RS** – a new product timestamp every 5 minutes with an expected publication delay of about 3 minutes.
* **RADOLAN RW** – a new product timestamp every 10 minutes with an expected publication delay of about 24 minutes.

HTTP requests use **ETag** and **Last-Modified** where available. If the DWD product has not changed, the server can respond with `304 Not Modified`, avoiding another transfer of the complete product file.

If an expected product is not yet available, the integration checks again every 30 seconds during the first five minutes. After that, the retry interval is increased to two minutes.

The 30-second coordinator interval is also required so that the real-time RV entities can move to the appropriate five-minute forecast interval as wall-clock time advances, even between two DWD publications.

### RW history and backfill

RADOLAN RW files are stored locally under `/config/dwd_rainradar`. The integration maintains the history required to calculate rolling precipitation totals.

After initial setup or when historical intervals are missing, available RW products are downloaded in the background. Backfill processing is independent of current sensor updates and does not block the Home Assistant event loop.

## Known limitations

* The integration is limited to the radar coverage of the DWD products used. Locations outside DWD radar coverage cannot be configured.
* Current data requires access to the public DWD Open Data service.
* RADVOR is a short-range radar-based nowcasting product and does not replace a general weather forecast.
* RV forecasts extend only approximately two hours into the future.
* RS hourly totals are anchored to the DWD analysis time. The next one and two hour sensors therefore do not exactly represent 60- or 120-minute periods starting at the current wall-clock time.
* The integration deliberately does not interpolate RS precipitation within an hourly interval.
* Immediately after initial setup, longer rolling RW totals may temporarily have no value until the required history has been backfilled.
* The current version provides precipitation amount and intensity but not precipitation type such as rain, snow, graupel or hail.

## Automation example

The following example creates a Home Assistant persistent notification when the **Precipitation active** binary sensor changes to `on`.

Replace the entity ID with the entity ID belonging to your configured location.

```yaml
alias: DWD Rain Radar – Precipitation starts
triggers:
  - trigger: state
    entity_id: binary_sensor.YOUR_LOCATION_precipitation_active
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      title: Precipitation detected
      message: DWD Rain Radar currently reports precipitation.
mode: single
```

The precipitation entities can also be used as conditions for irrigation, window, awning or other weather-dependent automations.

## Troubleshooting

### The integration cannot be set up

**Symptom:** The setup flow reports that it cannot connect to the DWD service.

**Resolution:**

1. Verify that Home Assistant has general internet access.
2. Verify that `https://opendata.dwd.de` can be reached from the Home Assistant system.
3. Check DNS, firewall, proxy or Pi-hole rules if the DWD service is being blocked.
4. If DWD is temporarily unavailable, retry setup later.

### Only some sensor groups are unavailable

If, for example, only RV entities are unavailable while RW and RS continue to work, the corresponding DWD product may have become stale.

Download diagnostics under **Settings → Devices & Services → DWD Rain Radar** and check which product is reported as `fresh: false`.

The affected entities automatically become available again as soon as DWD publishes a newer product.

### Rolling precipitation totals show `unknown`

The required RW history may still be incomplete, especially directly after initial setup.

The integration automatically downloads missing historical RW products in the background. Longer windows such as 24, 36 or 48 hours can therefore become available later than shorter windows.

If a value remains unknown, inspect the diagnostics for the backfill and product status.

### Expected entities are missing

Check the enabled sensor groups in the options of the DWD Rain Radar integration entry.

Entities belonging to a disabled sensor group are intentionally not created.

### The location or name needs to be changed

Open the integration entry and select **Reconfigure**. The integration does not need to be removed.

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

## Removal

The integration can be removed from **Settings → Devices & Services → DWD Rain Radar** using the menu of the corresponding entry.

Locally stored radar data remains in `/config/dwd_rainradar`. If all integration entries have been removed and the data is no longer needed, this directory can be deleted manually.

## Project History

DWD Rain Radar originated as a continuation of the [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) integration created by [@Hoffmann77](https://github.com/Hoffmann77).

When the German Weather Service (_Deutscher Wetterdienst_, DWD) migrated its radar products to HDF5, the original integration required substantial changes. This project started as a compatibility update and has since evolved into an independent integration with its own architecture, configuration flow and sensor model.

This README and the integration it documents have been substantially modified from the original DWD Precipitation project.

## License and Credits

DWD Rain Radar is released under the **Apache License, Version 2.0**.

The project originated from **DWD Precipitation** by [@Hoffmann77](https://github.com/Hoffmann77), which was distributed under the Apache License, Version 2.0. Files derived from that project have been substantially modified for DWD Rain Radar by Turavien since 2026.

Earlier versions of the radar processing incorporated adapted components of the **wradlib** project. The corresponding MIT license notice is retained in this repository:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback and Contributions

Bug reports, feature requests and pull requests are welcome through the GitHub repository.

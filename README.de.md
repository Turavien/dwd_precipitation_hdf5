# DWD Regenradar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_rainradar)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_rainradar)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_rainradar)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_rainradar)

🇬🇧 English version: [README.md](README.md)

> **Hinweis**
>
> Dies ist keine offizielle Integration des Deutschen Wetterdienstes (DWD).
>
> Das Projekt wird unabhängig entwickelt und steht in keiner Verbindung zum Deutschen Wetterdienst.
>
> Verwendet werden ausschließlich öffentlich verfügbare Open-Data-Produkte des DWD.

Diese Custom Integration für Home Assistant stellt hochaufgelöste Radar- und Niederschlagsdaten des Deutschen Wetterdienstes (DWD) bereit.

Sie kombiniert historische Niederschlagsanalysen (RADOLAN) mit kurzzeitigen Niederschlagsvorhersagen (RADVOR) und stellt speziell für Home-Assistant-Automatisierungen optimierte Sensoren bereit.

Typische Einsatzgebiete sind unter anderem:

* automatische Gartenbewässerung
* Warnungen vor einsetzendem Regen bei geöffneten Fenstern
* wetterabhängige Hausautomatisierungen

> **Wichtig**
>
> Die Vorhersagesensoren liefern die erwarteten Niederschlagssummen für die nächsten
>
> * 1 Stunde
> * 2 Stunden
> * 3 Stunden
>
> Die Werte geben also an, wie viel Niederschlag innerhalb dieses Zeitraums voraussichtlich insgesamt fallen wird.

## Funktionsweise

Die Daten basieren auf den offiziellen Radarprodukten des Deutschen Wetterdienstes.

Die verwendeten Raster besitzen eine räumliche Auflösung von etwa 1 km × 1 km und umfassen insgesamt 1100 × 1200 Rasterzellen.

Für den konfigurierten Standort wird automatisch diejenige Rasterzelle verwendet, deren Mittelpunkt dem angegebenen Standort am nächsten liegt.

Die Integration nutzt:

* RADOLAN RW
* RADOLAN SF
* RADVOR RS
* RADVOR RV

und stellt folgende Werte bereit:

* Gesamtniederschlag der letzten Stunde [mm]
* Gesamtniederschlag der letzten 24 Stunden [mm]

* erwarteter Niederschlag innerhalb der nächsten Stunde [mm]
* erwarteter Niederschlag innerhalb der nächsten 2 Stunden [mm]
* erwarteter Niederschlag innerhalb der nächsten 3 Stunden [mm]

* aktuelle Niederschlagsintensität [mm/h]
* erwartete Niederschlagsintensität in 5 Minuten [mm/h]
* erwartete Niederschlagsintensität in 10 Minuten [mm/h]
* erwartete Niederschlagsintensität in 15 Minuten [mm/h]
* Regenbeginn des nächsten Niederschlagsereignisses [min]
* Regenende des nächsten Niederschlagsereignisses [min]
* Regendauer des nächsten Niederschlagsereignisses [min]
* maximale Niederschlagsintensität des nächsten Niederschlagsereignisses [mm/h]
* Binary Sensor „Regen aktiv“

## Besonderheiten

Die Integration kombiniert mehrere offizielle Radarprodukte des Deutschen Wetterdienstes.

Je nach Sensor werden entweder

* gemessene Niederschlagssummen,
* prognostizierte Niederschlagssummen oder
* Niederschlagsintensitäten

bereitgestellt.

Die Vorhersagesummen basieren auf dem RADVOR-RS-Produkt und liefern die erwarteten Niederschlagsmengen für die nächsten 1 bis 3 Stunden.

Die Niederschlagsintensitäten basieren auf dem RADVOR-RV-Produkt und ermöglichen zusätzlich die Erkennung zusammenhängender Niederschlagsereignisse.

Hieraus werden folgende Ereignissensoren abgeleitet:

* Regen aktiv
* Regenbeginn
* Regenende
* Regendauer
* maximale Niederschlagsintensität des Niederschlagsereignisses

Dadurch eignet sich die Integration sowohl für Bewässerungssteuerungen als auch für Warnungen vor geöffneten Fenstern oder andere zeitkritische wetterabhängige Automatisierungen.

Die Integration funktioniert nur innerhalb Deutschlands sowie in grenznahen Bereichen, für die DWD-Radardaten verfügbar sind.

Koordinaten außerhalb des verfügbaren DWD-Radargebietes werden bereits bei der Konfiguration abgewiesen.

## Datenquellen

Alle Daten stammen vom Deutschen Wetterdienst (DWD).

### RADVOR RS

Radarbasierte Vorhersage der erwarteten Niederschlagssummen für jeweils ein einstündiges Vorhersagefenster.

### RADVOR RV

Radarbasierte Vorhersage der Niederschlagsintensität im 5-Minuten-Raster.

### RADOLAN RW

Radarbasierte Niederschlagsanalyse der letzten Stunde.

### RADOLAN SF

Radarbasierte Niederschlagsanalyse der letzten 24 Stunden.

## Installation über HACS

1. HACS öffnen
2. Benutzerdefinierte Repositories hinzufügen
3. Repository-URL eintragen
4. Kategorie „Integration“ auswählen
5. Integration installieren
6. Home Assistant neu starten

## Projektgeschichte

Dieses Projekt entstand ursprünglich als Weiterentwicklung der Integration [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) von [@Hoffmann77](https://github.com/Hoffmann77).

Nachdem der Deutsche Wetterdienst seine Radarprodukte auf HDF5 umgestellt hatte, wurde die ursprüngliche Integration zunächst angepasst und anschließend eigenständig weiterentwickelt.

Der ursprüngliche Ansatz bildet weiterhin die Grundlage des Projekts, während Architektur, Datenverarbeitung und Funktionsumfang inzwischen in weiten Teilen neu implementiert wurden.

## Lizenz und Hinweise

Teile der Radarverarbeitung basieren auf Komponenten des wradlib-Projektes.
Die wradlib-Lizenz befindet sich unter:
custom_components/dwd_rainradar/radar/LICENSE.txt

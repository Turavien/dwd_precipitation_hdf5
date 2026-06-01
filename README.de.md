# DWD Regenradar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_precipitation_hdf5)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_precipitation_hdf5)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_precipitation_hdf5)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_precipitation_hdf5)

🇬🇧 English version: [README.md](README.md)

# DWD Regenradar

> **Hinweis**
>
> Dies ist keine offizielle Integration des Deutschen Wetterdienstes (DWD).
>
> Das Projekt wird unabhängig entwickelt und steht in keiner Verbindung zum Deutschen Wetterdienst.
>
> Verwendet werden ausschließlich öffentlich verfügbare Open-Data-Produkte des DWD.

Diese Custom Integration für Home Assistant stellt hochaufgelöste Niederschlagsdaten des Deutschen Wetterdienstes (DWD) bereit.

Die Integration entstand als Weiterentwicklung der Integration [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation) von [@Hoffmann77](https://github.com/Hoffmann77), nachdem der DWD sein Datenformat auf HDF5 umgestellt hatte und DWD Precipitation dadurch zeitweise nicht mehr nutzbar war.

Im Zuge dieser Umstellung wurde der Code weitgehend überarbeitet und die bereitgestellten Entitäten an die eigenen Anforderungen angepasst, insbesondere für die automatisierte Steuerung einer Gartenbewässerung.

## Funktionsweise

Die Daten basieren auf den offiziellen Radarprodukten des Deutschen Wetterdienstes.

Die verwendeten Raster besitzen eine räumliche Auflösung von etwa 1 km × 1 km und umfassen insgesamt 1100 × 1200 Rasterzellen.

Für den konfigurierten Standort wird automatisch diejenige Rasterzelle verwendet, deren Mittelpunkt dem angegebenen Standort am nächsten liegt.

Die Integration nutzt:

* RADOLAN RW
* RADOLAN SF
* RADVOR RQ

und stellt folgende Werte bereit:

* Gesamtniederschlag der letzten Stunde [mm]
* Gesamtniederschlag der letzten 24 Stunden [mm]
* Kumulierte Niederschlagsvorhersagen [mm]

  * innerhalb der nächsten 5 Minuten
  * innerhalb der nächsten 10 Minuten
  * innerhalb der nächsten 15 Minuten
  * innerhalb der nächsten 30 Minuten
  * innerhalb der nächsten 45 Minuten
  * innerhalb der nächsten 60 Minuten
  * innerhalb der nächsten 90 Minuten
  * innerhalb der nächsten 120 Minuten

## Besonderheiten

Die Vorhersagewerte werden intern aus allen verfügbaren Fünf-Minuten-Intervallen der RADVOR-Daten kumuliert berechnet.

Dadurch liefert die Integration die tatsächlich erwarteten Niederschlagssummen in Millimetern [mm] und nicht lediglich die zu einem bestimmten Zeitpunkt erwartete Niederschlagsintensität [mm/h].

Die Integration funktioniert nur innerhalb Deutschlands sowie in grenznahen Bereichen, für die DWD-Radardaten verfügbar sind.

Koordinaten außerhalb des verfügbaren DWD-Radargebietes werden bereits bei der Konfiguration abgewiesen.

## Datenquellen

Alle Daten stammen vom Deutschen Wetterdienst (DWD).

### RADVOR RQ

Radarbasierte Niederschlagsvorhersage mit hoher zeitlicher und räumlicher Auflösung.

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

## Lizenz und Hinweise

Die ursprüngliche Integration wurde von [@Hoffmann77](https://github.com/Hoffmann77) veröffentlicht.
Diese Version wurde technisch umfassend und grundlegend überarbeitet und an die aktuelle Struktur der DWD-RADVOR-Daten angepasst.

Teile der Radarverarbeitung basieren auf Komponenten des wradlib-Projektes.
Die wradlib-Lizenz befindet sich unter:
custom_components/dwd_precipitation_hdf5/radar/LICENSE.txt

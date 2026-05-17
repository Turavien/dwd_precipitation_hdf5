# DWD Precipitation HDF5

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_precipitation_hdf5)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_precipitation_hdf5)
![License](https://img.shields.io/badge/license-MIT-green.svg)

[![Open your Home Assistant instance and open the repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Turavien&repository=dwd_precipitation_hdf5)

[![Open your Home Assistant instance and start setting up a new integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dwd_precipitation_hdf5)

🇬🇧 English version: [README.md](README.md)

Diese benutzerdefinierte Home-Assistant-Integration stellt hochaufgelöste Niederschlagsdaten des Deutschen Wetterdienstes (DWD) bereit.

Die Daten basieren auf Radar-Kompositen mit einer räumlichen Auflösung von etwa 1 km × 1 km.

Für den konfigurierten Standort wird automatisch die nächstgelegene Rasterzelle verwendet.

Die Integration nutzt:

- RADOLAN RW
- RADOLAN SF
- RADVOR RQ

und bietet:

- Niederschlag der letzten Stunde [mm]
- Niederschlag der letzten 24 Stunden [mm]
- kumulierte Niederschlagsvorhersagen [mm] für:
  - +5 Minuten
  - +10 Minuten
  - +15 Minuten
  - +30 Minuten
  - +45 Minuten
  - +60 Minuten
  - +90 Minuten
  - +120 Minuten

## Besonderheiten

Die Vorhersagewerte werden intern aus allen verfügbaren 5-Minuten-RADVOR-Intervallen kumuliert berechnet.

Die Integration liefert dadurch echte Niederschlagssummen in Millimeter [mm] und keine Momentanintensitäten [mm/h].

Die Integration funktioniert nur innerhalb Deutschlands sowie in grenznahen Bereichen, für die DWD-Radardaten verfügbar sind.

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

Die ursprüngliche Integration wurde von @Hoffmann77 veröffentlicht.

Diese Version wurde technisch umfassend überarbeitet und an die aktuelle Struktur der DWD-RADVOR-Daten angepasst.

Teile der Radarverarbeitung basieren auf Komponenten des wradlib-Projektes.

Die wradlib-Lizenz befindet sich unter:

custom_components/dwd_precipitation_hdf5/radar/LICENSE.txt

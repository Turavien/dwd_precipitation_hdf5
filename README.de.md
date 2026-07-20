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

Diese Custom Integration für Home Assistant stellt hochaufgelöste radarbasierte Niederschlagsdaten des Deutschen Wetterdienstes (DWD) bereit.

Sie kombiniert gemessene Niederschlagsanalysen (RADOLAN) mit kurzzeitigen Radarvorhersagen (RADVOR) und stellt die Daten als Home Assistant-Entitäten bereit.

Typische Einsatzgebiete sind:

* automatische Gartenbewässerung
* Warnungen vor einsetzendem Regen bei geöffneten Fenstern
* wetterabhängige Hausautomatisierungen
* wetterabhängige Steuerung von Rollläden, Markisen und Außengeräten

Die Integration wird vollständig über die Benutzeroberfläche von Home Assistant konfiguriert. Während der Einrichtung können die gewünschten Sensorgruppen ausgewählt werden. Sensorgruppen lassen sich später jederzeit über die Integrationsoptionen aktivieren oder deaktivieren, ohne dass die Integration entfernt und neu eingerichtet werden muss.

> **Wichtig**
>
> Die Vorhersagesensoren liefern die **erwarteten Niederschlagssummen** für die nächsten
>
> * 1 Stunde
> * 2 Stunden
> * 3 Stunden
>
> Jeder Wert beschreibt die Niederschlagsmenge, die innerhalb des jeweiligen Vorhersagezeitraums voraussichtlich insgesamt fallen wird. Es handelt sich **nicht** um momentane Niederschlagsintensitäten.

## Funktionen

* Hochaufgelöste radarbasierte Niederschlagsdaten des Deutschen Wetterdienstes (DWD)
* Kombination aus gemessenen Niederschlagsanalysen (RADOLAN) und kurzzeitigen Radarvorhersagen (RADVOR)
* Automatische Auswahl der nächstgelegenen Radarrasterzelle für den konfigurierten Standort
* Optionale Sensorgruppen
* Vollständige Konfiguration über den ConfigFlow und OptionsFlow von Home Assistant
* Berechnete gleitende Niederschlagssummen auf Basis offizieller DWD-Daten
* Home Assistant-Entitäten für gemessene, vorhergesagte und abgeleitete Niederschlagsdaten
* Automatische Entfernung von Entitäten deaktivierter Sensorgruppen
* Deutsche und englische Übersetzungen

## Funktionsweise

Die Integration basiert ausschließlich auf offiziellen Radarprodukten des Deutschen Wetterdienstes (DWD).

Die Radardaten liegen als Raster mit einer räumlichen Auflösung von etwa **1 km × 1 km** und einer Größe von **1100 × 1200** Rasterzellen vor.

Während der Einrichtung bestimmt die Integration automatisch die Radarrasterzelle, deren Mittelpunkt dem konfigurierten Standort am nächsten liegt. Alle Entitäten werden aus den Daten dieser Rasterzelle berechnet. Dadurch beziehen sich gemessene Werte, Vorhersagen und berechnete Entitäten stets auf denselben Standort.

Die Integration verwendet derzeit folgende DWD-Produkte:

* RADOLAN RW
* RADOLAN SF
* RADVOR RS
* RADVOR RV

Sie stellt folgende Entitäten bereit:

### Historischer Niederschlag

* Gesamtniederschlag der letzten Stunde [mm]
* Berechnete gleitende Niederschlagssumme der letzten 2 Stunden [mm]
* Berechnete gleitende Niederschlagssumme der letzten 3 Stunden [mm]
* Berechnete gleitende Niederschlagssumme der letzten 6 Stunden [mm]
* Berechnete gleitende Niederschlagssumme der letzten 12 Stunden [mm]
* Gesamtniederschlag der letzten 24 Stunden [mm]

### Niederschlagsvorhersage

* Erwartete Niederschlagssumme der nächsten Stunde [mm]
* Erwartete Niederschlagssumme der nächsten 2 Stunden [mm]
* Erwartete Niederschlagssumme der nächsten 3 Stunden [mm]

### Aktueller Niederschlag

* Aktuelle Niederschlagsintensität [mm/h]
* Erwartete Niederschlagsintensität in 5 Minuten [mm/h]
* Erwartete Niederschlagsintensität in 10 Minuten [mm/h]
* Erwartete Niederschlagsintensität in 15 Minuten [mm/h]
* Niederschlag aktiv (Binärsensor)

### Niederschlagsereignis

* Zeit bis zum nächsten Niederschlag [min]

## Eigenschaften

Die Integration kombiniert mehrere offizielle Radarprodukte des Deutschen Wetterdienstes in einem gemeinsamen Datenmodell.

Je nach Entität werden folgende Daten bereitgestellt:

* gemessene Niederschlagssummen (RADOLAN)
* vorhergesagte Niederschlagssummen (RADVOR RS)
* vorhergesagte Niederschlagsintensitäten (RADVOR RV)
* berechnete gleitende Niederschlagssummen auf Basis offizieller DWD-Messdaten

Alle Entitäten werden aus derselben Radarrasterzelle berechnet. Dadurch beziehen sich Messwerte, Vorhersagen und berechnete Entitäten stets auf denselben Standort.

Sensorgruppen können während der Einrichtung und später über die Integrationsoptionen einzeln aktiviert oder deaktiviert werden. Es werden nur die ausgewählten Sensorgruppen erstellt.

Typische Anwendungsgebiete sind:

* automatische Gartenbewässerung
* Warnungen vor einsetzendem Regen bei geöffneten Fenstern
* Schutz von Rollläden und Markisen
* wetterabhängige Steuerung von Außengeräten

Die Integration ist nur innerhalb Deutschlands sowie in grenznahen Bereichen verfügbar, die von den offiziellen DWD-Radarprodukten abgedeckt werden. Standorte außerhalb des unterstützten Radargebiets werden während der Konfiguration abgewiesen.

## Datenquellen

Alle Daten stammen aus öffentlich verfügbaren Open-Data-Produkten des Deutschen Wetterdienstes (DWD).

Die Integration verwendet derzeit vier offizielle Radarprodukte, die jeweils unterschiedliche Aufgaben erfüllen.

### RADOLAN RW

Radarbasierte Niederschlagsanalyse der letzten Stunde.

Dieses Produkt liefert die gemessene Niederschlagssumme der vergangenen Stunde und dient als Grundlage für die berechneten gleitenden Niederschlagssummen (2 h, 3 h, 6 h und 12 h).

### RADOLAN SF

Radarbasierte Niederschlagsanalyse der vergangenen 24 Stunden.

Dieses Produkt liefert die gemessene Niederschlagssumme der letzten 24 Stunden.

### RADVOR RS

Radarbasierte Vorhersage kumulierter Niederschlagssummen.

Dieses Produkt liefert die erwarteten Niederschlagssummen für die nächsten:

* 1 Stunde
* 2 Stunden
* 3 Stunden

### RADVOR RV

Radarbasierte Vorhersage der Niederschlagsintensität mit einer zeitlichen Auflösung von fünf Minuten.

Aus diesem Produkt werden folgende Entitäten abgeleitet:

* aktuelle Niederschlagsintensität
* erwartete Niederschlagsintensität in 5 Minuten
* erwartete Niederschlagsintensität in 10 Minuten
* erwartete Niederschlagsintensität in 15 Minuten
* berechneter Zeitpunkt des nächsten Niederschlags
* Binärsensor **„Niederschlag aktiv“**

## Installation über HACS

1. **HACS** öffnen.
2. Dieses Repository als **Benutzerdefiniertes Repository** hinzufügen.
3. Die Kategorie **Integration** auswählen.
4. **DWD Regenradar** installieren.
5. Home Assistant neu starten.

Nach dem Neustart:

1. Zu **Einstellungen → Geräte & Dienste** wechseln.
2. **Integration hinzufügen** auswählen.
3. Nach **DWD Regenradar** suchen.
4. Den gewünschten Standort eingeben oder auf der Karte auswählen.
5. Die gewünschten Sensorgruppen auswählen.
6. Die Einrichtung abschließen.

Die Sensorgruppen können später jederzeit über **Einstellungen → Geräte & Dienste → DWD Regenradar → Konfigurieren** geändert werden, ohne dass die Integration entfernt und erneut eingerichtet werden muss.

## Projektgeschichte

DWD Regenradar entstand als Fortführung der Integration [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation), die von [@Hoffmann77](https://github.com/Hoffmann77) entwickelt wurde.

Nachdem der Deutsche Wetterdienst (DWD) seine Radarprodukte auf das HDF5-Format umgestellt hatte, erforderte die ursprüngliche Integration umfangreiche Anpassungen. Dieses Projekt konzentrierte sich zunächst auf die Wiederherstellung der Kompatibilität und entwickelte sich anschließend schrittweise zu einer eigenständigen Integration.

Heute verfügt DWD Regenradar über eine eigene Architektur, einen eigenen Konfigurationsfluss, ein eigenes Sensormodell sowie eine eigenständige Entwicklungsroadmap und baut gleichzeitig auf den Ideen des ursprünglichen Projekts auf.

## Lizenz und Hinweise

Dieses Projekt wird unter der MIT-Lizenz veröffentlicht.

Teile der Radarverarbeitung basieren auf Komponenten des **wradlib**-Projekts.

Die entsprechende Lizenz befindet sich in diesem Repository unter:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback und Beiträge

Fehlerberichte, Funktionswünsche und Pull Requests können über GitHub eingereicht werden.

Fehler und Funktionswünsche können über den GitHub-Issue-Tracker gemeldet werden.

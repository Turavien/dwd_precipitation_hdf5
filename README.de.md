# DWD Regenradar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_rainradar)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_rainradar)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.3%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
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

Diese Custom Integration für Home Assistant stellt offizielle radarbasierte Niederschlagsdaten des Deutschen Wetterdienstes (DWD) bereit.

Sie kombiniert RADOLAN-Messungen mit RADVOR-Vorhersagen und erzeugt daraus Mess-, Vorhersage- und berechnete Entitäten für Home Assistant.

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
>
> Jeder Wert beschreibt die Niederschlagsmenge, die innerhalb des jeweiligen Vorhersagezeitraums voraussichtlich insgesamt fallen wird. Es handelt sich **nicht** um momentane Niederschlagsintensitäten.

## Screenshots

### Integration

![Integration](images/de/integration.png)

### Optionen

![Options](images/de/options.png)

### Entitäten

![Entities](images/de/entities.png)

## Funktionen

* Offizielle DWD-Radarprodukte (RADOLAN & RADVOR)
* Gemessene, vorhergesagte und berechnete Niederschlagsdaten
* Automatische Auswahl der passenden Radarrasterzelle
* Optionale Sensorgruppen
* Niederschlagssummen bis 48 Stunden
* Einrichtung und Optionen vollständig über die Home-Assistant-Oberfläche
* Automatische Bereinigung nicht mehr angebotener Entitäten
* Deutsche und englische Übersetzungen

## Funktionsweise

Die Integration verwendet ausschließlich offizielle Radarprodukte des Deutschen Wetterdienstes (DWD).

Die Radardaten liegen auf einem Raster von etwa **1 km × 1 km**. Während der Einrichtung wird automatisch die nächstgelegene Rasterzelle ausgewählt, aus der anschließend alle Entitäten berechnet werden.

Die Integration verwendet folgende DWD-Produkte:

* RADOLAN RW
* RADVOR RS
* RADVOR RV

Sie stellt folgende Entitäten bereit:

### Historischer Niederschlag

* Niederschlag der letzten Stunde [mm]
* Niederschlag der letzten 2 Stunden [mm]
* Niederschlag der letzten 3 Stunden [mm]
* Niederschlag der letzten 6 Stunden [mm]
* Niederschlag der letzten 9 Stunden [mm]
* Niederschlag der letzten 12 Stunden [mm]
* Niederschlag der letzten 24 Stunden [mm]
* Niederschlag der letzten 36 Stunden [mm]
* Niederschlag der letzten 48 Stunden [mm]

### Niederschlagsvorhersage

* Erwartete Niederschlagssumme der nächsten Stunde [mm]
* Erwartete Niederschlagssumme der nächsten 2 Stunden [mm]

### Niederschlagsintensität

* Aktuelle Niederschlagsintensität [mm/h]
* Erwartete Niederschlagsintensität in 5 Minuten [mm/h]
* Erwartete Niederschlagsintensität in 10 Minuten [mm/h]
* Erwartete Niederschlagsintensität in 15 Minuten [mm/h]
* Max. erwartete Niederschlagsintensität der nächsten 2 Stunden [mm/h]

### Niederschlagsereignis

* Zeit bis zum nächsten erwarteten Niederschlag [min]
* Niederschlag aktiv (Binärsensor)

## Datenquellen

Alle Daten stammen aus öffentlich verfügbaren Open-Data-Produkten des Deutschen Wetterdienstes (DWD), die jeweils unterschiedliche Aufgaben erfüllen.

### RADOLAN RW

Radarbasierte, angeeichte Niederschlagssumme über jeweils eine Stunde.

RW wird in überlappenden Zeitfenstern veröffentlicht. Die Integration hält die benötigte RW-Historie lokal vor und wählt daraus für jede Berechnung eine lückenlose Folge nicht überlappender Stundenintervalle. Daraus entstehen die Niederschlagssummen für 1 h, 2 h, 3 h, 6 h, 9 h, 12 h, 24 h, 36 h und 48 h.

### RADVOR RS

Radarbasierte einstündige Niederschlagsvorhersage, die alle fünf Minuten für unterschiedliche Vorhersagezeitpunkte bereitgestellt wird.

Für die nächste Stunde verwendet die Integration das Intervall von jetzt bis +60 Minuten. Für die nächsten zwei Stunden werden die beiden nicht überlappenden Intervalle 0–60 und 60–120 Minuten addiert.

### RADVOR RV

Radarbasierte Niederschlagsvorhersage in Fünf-Minuten-Intervallen für die kommenden 120 Minuten.

Die Integration verwendet das Intervall, das am aktuellen Zeitpunkt endet, für die aktuelle Intensität. Die Vorhersagen in 5, 10 und 15 Minuten beziehen sich jeweils auf das dort endende Fünf-Minuten-Intervall. Die Niederschlagsmenge jedes Intervalls wird in eine äquivalente Intensität in mm/h umgerechnet. Daraus entstehen außerdem der Binärsensor **„Niederschlag aktiv“**, die Zeit bis zum nächsten erwarteten Niederschlag sowie die höchste erwartete Intensität.

## Installation über HACS

1. **HACS** öffnen.
2. Dieses Repository als **Benutzerdefiniertes Repository** hinzufügen.
3. Die Kategorie **Integration** auswählen.
4. **DWD Rain Radar** installieren.
5. Home Assistant neu starten.

Nach dem Neustart:

1. Zu **Einstellungen → Geräte & Dienste** wechseln.
2. **Integration hinzufügen** auswählen.
3. Nach **DWD Regenradar** suchen.
4. Den gewünschten Standort eingeben oder auf der Karte auswählen.
5. Die gewünschten Sensorgruppen auswählen.
6. Die Einrichtung abschließen.

## Entfernen

Die Integration kann unter **Einstellungen → Geräte & Dienste → DWD Regenradar** über das Menü des jeweiligen Eintrags entfernt werden.

Die lokal gespeicherten Radardaten bleiben unter `/config/dwd_rainradar` erhalten. Wenn alle Einträge der Integration entfernt wurden und die Daten nicht mehr benötigt werden, kann dieses Verzeichnis manuell gelöscht werden.

## Projektgeschichte

DWD Regenradar entstand als Fortführung der Integration [DWD Precipitation](https://github.com/Hoffmann77/ha-dwd-precipitation), die von [@Hoffmann77](https://github.com/Hoffmann77) entwickelt wurde.

Nachdem der Deutsche Wetterdienst (DWD) seine Radarprodukte auf das HDF5-Format umgestellt hatte, erforderte die ursprüngliche Integration umfangreiche Anpassungen. Dieses Projekt konzentrierte sich zunächst auf die Wiederherstellung der Kompatibilität und entwickelte sich anschließend schrittweise zu einer eigenständigen Integration mit eigener Architektur, Konfigurationsfluss und Sensormodell.

## Lizenz und Hinweise

Dieses Projekt wird unter der MIT-Lizenz veröffentlicht.

Teile der Radarverarbeitung basieren auf Komponenten des **wradlib**-Projekts.

Die entsprechende Lizenz befindet sich in diesem Repository unter:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback und Beiträge

Fehlerberichte, Funktionswünsche und Pull Requests können über GitHub eingereicht werden.

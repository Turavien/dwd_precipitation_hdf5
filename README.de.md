# DWD Regenradar

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/Turavien/dwd_rainradar)
![GitHub last commit](https://img.shields.io/github/last-commit/Turavien/dwd_rainradar)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.3%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)

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

Die Integration wird vollständig über die Benutzeroberfläche von Home Assistant konfiguriert.

## Konfiguration

### Einrichtung

Bei der erstmaligen Einrichtung werden folgende Angaben abgefragt:

* **Name** – Anzeigename des Standorts in Home Assistant.
* **Standort** – Breiten- und Längengrad des auszuwertenden Standorts. Der Standort kann über die Home-Assistant-Standortauswahl gewählt werden. Die Integration berechnet daraus automatisch die passende DWD-Rasterzelle.
* **Sensorgruppen** – legt fest, welche Entitäten für diesen Standort angelegt werden.

Folgende Sensorgruppen stehen zur Verfügung:

* **Intensitäten** – aktuelle Intensität, +5, +10 und +15 Minuten sowie die maximale erwartete Intensität der nächsten zwei Stunden.
* **Vorhersagemengen** – erwartete Niederschlagssummen der nächsten ein und zwei Stunden.
* **Niederschlagsereignis** – Niederschlag aktiv und Zeit bis zum nächsten erwarteten Niederschlag.
* **Menge letzte 1 Stunde** – jüngste RADOLAN-RW-Stundensumme.
* **Rollierende Mengen** – Niederschlagssummen der vergangenen 2 bis 48 Stunden.

### Optionen

Über die Optionen des Integrationseintrags können die aktivierten Sensorgruppen jederzeit geändert werden. Nicht mehr ausgewählte Entitäten werden automatisch aus der Entity Registry entfernt.

### Neu konfigurieren

Über **Neu konfigurieren** können Name und Standort eines bestehenden Eintrags geändert werden, ohne die Integration zu entfernen und erneut einzurichten.

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

Datenbasis: Deutscher Wetterdienst (DWD), Open Data. Die von dieser Integration bereitgestellten Werte werden aus diesen Ausgangsprodukten verarbeitet und abgeleitet.

Alle Daten stammen aus öffentlich verfügbaren Open-Data-Produkten des Deutschen Wetterdienstes (DWD), die jeweils unterschiedliche Aufgaben erfüllen.

### RADOLAN RW

Radarbasierte, angeeichte Niederschlagssumme über jeweils eine Stunde.

RW wird in überlappenden Zeitfenstern veröffentlicht. Die Integration hält die benötigte RW-Historie lokal vor und wählt daraus für jede Berechnung eine lückenlose Folge nicht überlappender Stundenintervalle. Daraus entstehen die Niederschlagssummen für 1 h, 2 h, 3 h, 6 h, 9 h, 12 h, 24 h, 36 h und 48 h.

### RADVOR RS

Radarbasierte einstündige Niederschlagsvorhersage, die alle fünf Minuten für unterschiedliche Vorhersagezeitpunkte bereitgestellt wird.

Für die Sensoren der nächsten ein beziehungsweise zwei Stunden verwendet die Integration die ersten ein beziehungsweise zwei nicht überlappenden 60-Minuten-Vorhersageintervalle des jeweils neuesten DWD-Laufs. Diese Intervalle sind an den DWD-Analysezeitpunkt gebunden. Wegen der Bereitstellungsverzögerung des Produkts entsprechen sie daher nicht exakt einem von der aktuellen Uhrzeit aus verschobenen 60- beziehungsweise 120-Minuten-Zeitraum. Eine zeitliche Interpolation innerhalb eines Stundenintervalls wird bewusst nicht vorgenommen.

### RADVOR RV

Radarbasierte Niederschlagsvorhersage in Fünf-Minuten-Intervallen für die kommenden 120 Minuten.

Für die aktuelle Intensität verwendet die Integration das RV-Fünf-Minuten-Intervall, das den tatsächlichen aktuellen Zeitpunkt enthält. Die Vorhersagen in 5, 10 und 15 Minuten verwenden entsprechend die Intervalle, welche die reale aktuelle Uhrzeit plus 5, 10 beziehungsweise 15 Minuten enthalten. Dadurch schreiten diese Sensoren auch zwischen zwei DWD-Veröffentlichungen mit der realen Zeit fort. Die Niederschlagsmenge jedes Intervalls wird in eine äquivalente Intensität in mm/h umgerechnet. Daraus entstehen außerdem der Binärsensor **„Niederschlag aktiv“**, die reale Zeit bis zum nächsten erwarteten Niederschlag sowie die höchste im noch verfügbaren RV-Vorhersagezeitraum erwartete Intensität.

## Datenaktualität und Verfügbarkeit

Die Integration bewertet die Aktualität von RW, RS und RV unabhängig voneinander. Ein Produkt gilt bis zu seinem nächsten erwarteten Veröffentlichungszeitpunkt einschließlich der bekannten Bereitstellungsverzögerung und einer zusätzlichen Toleranz von fünf Minuten als aktuell. Mit den derzeit verwendeten DWD-Zeitparametern entspricht dies etwa 39 Minuten für RW und 13 Minuten für RS beziehungsweise RV, jeweils bezogen auf den Zeitstempel des letzten empfangenen Produkts.

Bleibt nur eines der Produkte darüber hinaus unverändert, werden ausschließlich die davon abhängigen Entitäten als **nicht verfügbar** markiert. Andere Sensorgruppen bleiben nutzbar, solange deren eigenes DWD-Produkt aktuell ist. Sobald wieder ein neuer Produktstand vorliegt, werden die betroffenen Entitäten automatisch wieder verfügbar. Ein vollständiger Verbindungsfehler zum DWD wird weiterhin zentral über den Home-Assistant-Update-Coordinator behandelt.

## Diagnosedaten

Home Assistant kann für jeden Eintrag der Integration Diagnosedaten erzeugen. Sie können über das Menü des Integrationseintrags unter **Einstellungen → Geräte & Dienste → DWD Regenradar** heruntergeladen und beispielsweise einem Fehlerbericht beigefügt werden.

Die Diagnosedaten enthalten unter anderem:

* Status des Home-Assistant-Update-Coordinators
* Zeitstempel und Aktualitätsstatus von RW, RS und RV
* Veröffentlichungs- und Freshness-Zeitfenster der verwendeten DWD-Produkte
* öffentliche HTTP-Metadaten wie ETag und Last-Modified
* Anzahl registrierter Rasterzellen und Config-Entry-Referenzen
* Zustand der internen State- und Rolling-Caches
* Status laufender RW-Backfill-Aufgaben

Aus Datenschutzgründen werden **keine Standortdaten** ausgegeben. Insbesondere enthalten die Diagnosedaten weder Name noch Breiten- oder Längengrad noch die konkrete DWD-Rasterzelle des konfigurierten Standorts.

## Datenaktualisierung

Der Home-Assistant-Update-Coordinator der Integration läuft alle **30 Sekunden**. Dies bedeutet jedoch nicht, dass alle 30 Sekunden Dateien vom DWD heruntergeladen werden.

Die Integration kennt den Veröffentlichungsrhythmus der einzelnen Produkte und führt einen externen Abruf nur dann aus, wenn ein neuer Produktstand erwartet werden kann.

Aktuell werden folgende Zeitparameter verwendet:

* **RADVOR RV** – neuer Produktzeitpunkt alle 5 Minuten, üblicherweise mit etwa 3 Minuten Bereitstellungsverzögerung.
* **RADVOR RS** – neuer Produktzeitpunkt alle 5 Minuten, üblicherweise mit etwa 3 Minuten Bereitstellungsverzögerung.
* **RADOLAN RW** – neuer Produktzeitpunkt alle 10 Minuten, üblicherweise mit etwa 24 Minuten Bereitstellungsverzögerung.

HTTP-Anfragen verwenden nach Möglichkeit **ETag** und **Last-Modified**. Ist die beim DWD vorhandene Datei unverändert, kann der Server mit `304 Not Modified` antworten und die eigentliche Produktdatei muss nicht erneut übertragen werden.

Wird ein erwartetes neues Produkt nicht sofort bereitgestellt, prüft die Integration während der ersten fünf Minuten alle 30 Sekunden erneut. Danach wird das Prüfintervall auf zwei Minuten verlängert.

Die 30-sekündliche Coordinator-Aktualisierung wird außerdem benötigt, damit die realzeitbezogenen RV-Sensoren auch zwischen zwei DWD-Veröffentlichungen auf das jeweils zur aktuellen Uhrzeit passende Fünf-Minuten-Intervall wechseln können.

### RW-Historie und Backfill

RADOLAN-RW-Dateien werden lokal unter `/config/dwd_rainradar` gespeichert. Die Integration hält daraus die für rollierende Niederschlagssummen benötigte Historie vor.

Nach einer Neueinrichtung oder wenn historische Intervalle fehlen, lädt die Integration verfügbare RW-Produkte im Hintergrund nach. Der Backfill erfolgt unabhängig von den aktuellen Sensoraktualisierungen und blockiert Home Assistant nicht.

## Bekannte Einschränkungen

* Die Integration ist auf das Radargebiet der verwendeten DWD-Produkte beschränkt. Standorte außerhalb der DWD-Radarabdeckung können nicht eingerichtet werden.
* Für aktuelle Daten ist eine Verbindung zum öffentlichen DWD-Open-Data-Dienst erforderlich.
* RADVOR ist ein kurzfristiges radar-basiertes Nowcasting-Produkt und ersetzt keine allgemeine Wettervorhersage.
* Die RV-Vorhersage reicht maximal ungefähr zwei Stunden in die Zukunft.
* Die RS-Stundensummen sind an den Analysezeitpunkt des DWD gebunden. Die Sensoren „nächste 1 Stunde“ und „nächste 2 Stunden“ entsprechen deshalb nicht exakt einem ab der aktuellen Uhrzeit verschobenen 60- beziehungsweise 120-Minuten-Zeitraum.
* Die Integration interpoliert RS-Niederschlagsmengen bewusst nicht innerhalb eines Stundenintervalls.
* Direkt nach der ersten Einrichtung können größere rollierende RW-Summen vorübergehend noch keinen Wert liefern, bis die benötigte Historie im Hintergrund vervollständigt wurde.
* Die derzeitige Version stellt Niederschlagsmenge und Niederschlagsintensität bereit, aber noch keine Niederschlagsart wie Regen, Schnee, Graupel oder Hagel.

## Automationsbeispiel

Das folgende Beispiel erzeugt eine Home-Assistant-Benachrichtigung, sobald der Binärsensor **Niederschlag aktiv** auf `on` wechselt.

Die Entity-ID muss durch die Entity-ID des eigenen Standorts ersetzt werden.

```yaml
alias: DWD Regenradar – Niederschlag beginnt
triggers:
  - trigger: state
    entity_id: binary_sensor.DEIN_STANDORT_niederschlag_aktiv
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      title: Niederschlag erkannt
      message: DWD Regenradar meldet aktuell Niederschlag.
mode: single
```

Die Sensoren können ebenso als Bedingungen für Bewässerungs-, Fenster-, Markisen- oder andere wetterabhängige Automationen verwendet werden.

## Fehlerbehebung

### Die Integration lässt sich nicht einrichten

**Symptom:** Während der Einrichtung erscheint eine Meldung, dass keine Verbindung zum DWD hergestellt werden kann.

**Prüfung und Lösung:**

1. Prüfen, ob Home Assistant grundsätzlich Internetzugriff besitzt.
2. Prüfen, ob `https://opendata.dwd.de` vom Home-Assistant-System erreichbar ist.
3. DNS-, Firewall-, Proxy- oder Pi-hole-Regeln prüfen, falls der DWD-Dienst blockiert wird.
4. Besteht nur eine vorübergehende Störung beim DWD, die Einrichtung später erneut versuchen.

### Nur einzelne Sensorgruppen sind nicht verfügbar

Wenn beispielsweise nur RV-Entitäten nicht verfügbar sind, während RW und RS weiter funktionieren, kann das entsprechende DWD-Produkt veraltet sein.

Unter **Einstellungen → Geräte & Dienste → DWD Regenradar → Diagnose herunterladen** kann geprüft werden, welches Produkt als `fresh: false` geführt wird.

Sobald der DWD einen neuen Produktstand bereitstellt, werden die betreffenden Entitäten automatisch wieder verfügbar.

### Rollierende Niederschlagssummen zeigen `unknown`

Insbesondere direkt nach der Einrichtung kann die notwendige RW-Historie noch unvollständig sein.

Die Integration lädt fehlende historische RW-Produkte automatisch im Hintergrund nach. Größere Zeitfenster wie 24, 36 oder 48 Stunden können daher später verfügbar werden als die jüngeren Zeitfenster.

Bleibt ein Wert dauerhaft unbekannt, sollten die Diagnosedaten auf fehlende oder laufende Backfill-Daten geprüft werden.

### Erwartete Entitäten fehlen

Unter **Einstellungen → Geräte & Dienste → DWD Regenradar → Konfigurieren** beziehungsweise den Optionen des Integrationseintrags prüfen, welche Sensorgruppen aktiviert sind.

Entitäten einer deaktivierten Sensorgruppe werden bewusst nicht bereitgestellt.

### Standort oder Name sollen geändert werden

Den Integrationseintrag öffnen und **Neu konfigurieren** auswählen. Die Integration muss dafür nicht entfernt werden.

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

Diese README und die darin beschriebene Integration wurden gegenüber dem ursprünglichen Projekt DWD Precipitation wesentlich verändert.

## Lizenz und Hinweise

DWD Regenradar wird unter der **Apache License, Version 2.0** veröffentlicht.

Das Projekt entstand aus **DWD Precipitation** von [@Hoffmann77](https://github.com/Hoffmann77), das unter der Apache License, Version 2.0 veröffentlicht wurde. Aus diesem Projekt hervorgegangene Dateien wurden seit 2026 von Turavien für DWD Regenradar wesentlich verändert.

Frühere Versionen der Radarverarbeitung enthielten angepasste Komponenten des **wradlib**-Projekts. Der zugehörige MIT-Lizenzhinweis bleibt in diesem Repository erhalten:

```text
custom_components/dwd_rainradar/radar/LICENSE.txt
```

## Feedback und Beiträge

Fehlerberichte, Funktionswünsche und Pull Requests können über GitHub eingereicht werden.

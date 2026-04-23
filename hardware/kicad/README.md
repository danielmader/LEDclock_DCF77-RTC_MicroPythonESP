# KiCad files (Lochraster-Variante)

Dieses Verzeichnis enthaelt ein minimales KiCad-Projekt fuer die Schaltung
"5V High-Side mit sicherer 3.3V GPIO-Ansteuerung, Default EIN".

Dateien:
- esp_power_switch_default_on.kicad_pro
- esp_power_switch_default_on.kicad_sch
- esp_power_switch_default_on.kicad_pcb

Hinweise fuer Lochraster:
- Alle Widerstaende sind auf axiale THT-Footprints gesetzt.
- Q2/Q3 sind auf TO-92 gesetzt, Pinout im Datenblatt pruefen.
- Q1 ist auf TO-220 gesetzt. Bei anderem Pinout Source/Drain entsprechend verdrahten.
- Das PCB ist als Placement-Template gedacht (2.54 mm Raster), nicht als Fertigungs-PCB.

Konkrete Bestueckung auf der Template-Platine:
- J1 links oben: Eingang +5V/GND
- J2 rechts oben: Ausgang +V_BAUTEIL/GND
- J3 links mittig: ESP_GPIO, +5V, GND
- Q1 (TO-220) rechts oben
- Q3 (TO-92, PNP) mittig oben
- Q2 (TO-92, NPN) links mittig
- R5 zwischen Q3-Kollektor und Q1-Gate (Gate-Serie)
- R1 von Q1-Gate nach GND (Default EIN)
- R2 von +5V nach Q3-Basis
- R3 vom ESP_GPIO zu Q2-Basis
- R4 von Q2-Basis nach GND

Drahtbruecken (Lochraster, Unterseite):
- +5V: J1.1 -> J3.2 -> Q1.S -> R2.1 -> Q3.E
- GND: J1.2 -> J2.2 -> J3.3 -> Q2.E -> R1.2 -> R4.2
- GPIO: J3.1 -> R3.1
- Q2-Basis-Knoten: R3.2 -> Q2.B -> R4.1
- Q3-Basis-Knoten: R2.2 -> Q3.B -> Q2.C
- Q3-Kollektor-Knoten: Q3.C -> R5.1
- Q1-Gate-Knoten: Q1.G -> R5.2 -> R1.1
- Ausgang: Q1.D -> J2.1

Inbetriebnahme-Test:
- GPIO als Input (Hi-Z): Ausgang EIN
- GPIO auf LOW: Ausgang EIN
- GPIO auf HIGH: Ausgang AUS

Empfohlene Praxis fuer den Aufbau:
- 2-polige Klemmenleisten fuer IN (+5V/GND) und OUT (+V_BAUTEIL/GND).
- Sternfoermige Massefuehrung zwischen ESP-GND, Last-GND und Schaltstufe.
- Kurze Verbindung Gate-Netz (Q1_GATE) und 100 nF nah an der Last.

Schaltlogik:
- GPIO HIGH => AUS
- GPIO LOW oder Hi-Z => EIN (Default)

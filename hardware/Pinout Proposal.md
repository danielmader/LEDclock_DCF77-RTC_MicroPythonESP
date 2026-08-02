# Pinbelegungs-Dokumentation: ESP-WROOM-32 vs. ESP32-S3-WROOM-1

Beim Upgrade vom klassischen **ESP-WROOM-32** auf den neueren **ESP32-S3-WROOM-1** ändern sich einige Hardware-Peripherien und Standard-Pinbelegungen. Dank der flexiblen **GPIO-Matrix** (GPIO Mux) des ESP32 lassen sich viele Signale im Code frei auf andere Pins umleiten. Dennoch müssen spezifische Board-Eigenschaften (Strapping-Pins, USB-Interfaces, Octal-PSRAM) beachtet werden.

---

## 1. I2C-Bus (Temperatur-Sensor SHT31 & RTC RV-8263)

Beide I2C-Sensoren liegen parallel als Bus-Teilnehmer an denselben zwei Leitungen (`SDA` und `SCL`).

* **ESP-WROOM-32 (Standard):** `GPIO 23` (SDA) und `GPIO 22` (SCL).
* **ESP32-S3 (Standard):** `GPIO 8` (SDA) und `GPIO 9` (SCL).
* **Begründung & Wahl:**
  Beim Wechsel auf den ESP32-S3 wurden die neuen Hardware-Defaults **GPIO 8 (SDA)** und **GPIO 9 (SCL)** übernommen. Diese Pins sind frei von Strapping-Funktionen und ideal für I2C geeignet.

---

## 2. ADC / Analog-Eingang (TEMT6000 Helligkeitssensor)

Der analoge Lichtsensor benötigt einen ADC-Pin.

* **ESP-WROOM-32:** `GPIO 36` (VP / ADC1_CH0).
* **ESP32-S3:** `GPIO 4` (ADC1_CH3).
* **Begründung & Wahl:**
  Auf beiden Boards muss zwingend ein Kanal des **ADC1** gewählt werden, da ADC2 deaktiviert wird, sobald Wi-Fi aktiv genutzt wird. Beim ESP32-S3 fällt die Wahl auf **GPIO 4**, was ein unproblematischer ADC1-Eingang ist.
  *(Hinweis: Pins wie GPIO 35–37 dürfen beim S3-Board keinesfalls genutzt werden – siehe Abschnitt 6).*

---

## 3. GPIO Input (DCF77-Zeitsignal)

Das DCF77-Signal ist sehr langsam und benötigt keinen speziellen Hardware-Schnittstellen-Pin.

* **ESP-WROOM-32:** `GPIO 13`.
* **ESP32-S3:** `GPIO 14`.
* **Begründung & Wahl:**
  Auf beiden Boards wird ein Standard-GPIO genutzt. Auf dem S3-Board fällt die Wahl auf **GPIO 14**.
  *_Tipp: DCF77-Empfänger reagieren empfindlich auf Wi-Fi-Störungen und sollten räumlich getrennt vom ESP32 platziert werden._*

---

## 4. SPI-Bus (MAX7219 LED-Matrix)

Für die Übertragung an die LED-Matrix werden MOSI (Data), SCLK (Clock) und CS (Chip Select) benötigt.

* **ESP-WROOM-32 (Bisher):** `GPIO 19` (MOSI), `GPIO 5` (SCLK), `GPIO 18` (CS).
* **ESP32-S3 (Standard vs. Gewählt):**
  * *S3-Defaults:* `GPIO 11` (MOSI), `GPIO 12` (SCLK), `GPIO 10` (CS).
  * *Gewählte Ausweich-Pins:* **`GPIO 42` (MOSI)**, **`GPIO 1` (SCLK)**, **`GPIO 2` (CS)**.
* **Begründung der Abweichung:**
  * **Warum nicht GPIO 19, 20, 21 vom alten Board?** Beim ESP32-S3 sind GPIO 19 (`USB_D-`) und GPIO 20 (`USB_D+`) für das native USB-Interface reserviert. Eine Belegung führt zu Konflikten beim Flashen und Debuggen.
  * **Warum GPIO 1, 2, 42?** Diese Pins liegen auf der rechten Board-Seite direkt nebeneinander und bieten eine hervorragende Platine-Leitungsführung. Es handelt sich um vollwertige Digital-IOs ohne störende Strapping- oder System-Konflikte.

---

## 5. Display-Schalter (MAX7219 Power Cutoff / OFF)

Pin zur Ansteuerung des Versorgungsspannungsschalters für die Matrix.

* **ESP-WROOM-32 (Bisher angedacht):** `GPIO 0`.
* **ESP32-S3 (Gewählt):** `GPIO 21`.
* **Begründung & Korrektur:**
  * **Korrektur zu GPIO 0:** `GPIO 0` ist auf beiden Chips ein kritischer **Strapping-Pin** (Bootloader-Auswahl). Wird er beim Starten extern auf GND gezogen, schaltet der ESP in den Boot-Modus und startet den Code nicht.
  * **Wahl von GPIO 21:** Auf dem ESP32-S3 ist **GPIO 21** ein vollkommen freier Digital-Pin (RTC-fähig, aber ohne Boot-Einfluss). Er eignet sich ideal, um das Display sicher ein- und auszuschalten.

---

## 6. Wichtiger Sonderhinweis: Octal-PSRAM (N16R8)

Auf dem vorliegenden ESP32-S3-Modul ist die Variante **ESP32-S3-WROOM-1 N16R8** verbaut.

* **8 MB PSRAM = Octal SPI (OPI):** Bei allen ESP32-S3 mit 8 MB PSRAM belegt der RAM-Speicher intern fest die Pins **GPIO 33 bis GPIO 37**.
* **Auswirkung:** Die Pins GPIO 35, 36 und 37, die auf dem Pinout rausgeführt sind, dürfen **nicht extern beschaltet werden**! Eine Nutzung führt zum Absturz des Systems.

---

## 7. Zusammenfassende Pinbelegungs-Tabellen

### Board 1: ESP-WROOM-32 (Alt)

| Funktion / Peripherie | Signal / Rolle | Standard-Pin | Gewählter Pin | Anmerkung |
| :--- | :--- | :--- | :--- | :--- |
| **I2C-Bus** | SDA | GPIO 23 | **GPIO 23** | Standard I2C |
| | SCL | GPIO 22 | **GPIO 22** | Standard I2C |
| **ADC** | TEMT6000 | GPIO 36 | **GPIO 36** | ADC1_CH0 |
| **GPIO In** | DCF77 Signal | - | **GPIO 13** | Standard GPIO |
| **SPI-Bus** | MOSI (DIN) | GPIO 23 | **GPIO 19** | Per Hardware-Matrix umgeleitet |
| | SCLK | GPIO 18 | **GPIO 5** | Per Hardware-Matrix umgeleitet |
| | CS | GPIO 5 | **GPIO 18** | Per Hardware-Matrix umgeleitet |
| **Power-Control** | MAX7219 OFF | - | **GPIO 0** | *Kritisch:* Strapping-Pin! |

---

### Board 2: ESP32-S3-WROOM-1 (Neu, N16R8)

| Funktion / Peripherie | Signal / Rolle | Standard-Pin (FSPI/I2C) | Gewählter Pin | Anmerkung & Grund für Wahl |
| :--- | :--- | :--- | :--- | :--- |
| **I2C-Bus** | SDA | GPIO 8 | **GPIO 8** | S3-I2C Standard |
| | SCL | GPIO 9 | **GPIO 9** | S3-I2C Standard |
| **ADC** | TEMT6000 | GPIO 4 | **GPIO 4** | ADC1_CH3 (Sicher vor Wi-Fi-Konflikten) |
| **GPIO In** | DCF77 Signal | - | **GPIO 14** | Standard-GPIO |
| **SPI-Bus** | MOSI (DIN) | GPIO 11 | **GPIO 42** | Meidet GPIO 19/20 (USB) |
| | SCLK | GPIO 12 | **GPIO 1** | Meidet GPIO 19/20 (USB) |
| | CS | GPIO 10 | **GPIO 2** | Meidet GPIO 19/20 (USB) |
| **Power-Control** | MAX7219 OFF | - | **GPIO 21** | Sicherer Ersatz für GPIO 0 (Kein Boot-Pin) |

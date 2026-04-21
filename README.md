# LEDclock_DCF77-RTC_MicroPythonESP


Batterie-Backup für RV-8263 RTC
-------------------------------

    ESP-WROOM-32 NodeMCU

    VCC (3.3V ESP) -----------------+-------+-------+
                                    |       |       |
                                    [R1]    [R2]    [D1] (Schottky)
                                    10k     10k     |
                                    |       |       |
    SDA (GPIO 23) ------------------+----------------------- SDA (RV-8263)
                                            |       |
    SCL (GPIO 22) --------------------------+--------------- SCL (RV-8263)
                                                    |
                                                    +------- VCC (RV-8263)
                                                    |
    Batterie (+) ----------[D2] (Schottky) ---------+
    (Knopfzelle)

    GND (ESP) --------------------------------------+------- VSS (RV-8263)
                                                    |
    Batterie (-) -----------------------------------+


Schaltbild Peripherie (ohne Backup-Batterie)
--------------------------------------------

    ESP-WROOM-32 NodeMCU

    3V3  -----------------------------------+------------------+------------------+
                                            |                  |                  |
                                            |                  |                  +---- VCC (MAX7219)
                                            |                  +----------------------- VCC (TEMT6000)
                                            +------------------------------------------ VCC (I2C: RV-8263, SHT31)

    5V (VIN) --------------------------------------------------- VCC (DCF77)

    GND  -----------------------------------+------------------+------------------+------------------+
                                            |                  |                  |                  |
                                            |                  |                  |                  +---- GND (MAX7219)
                                            |                  |                  +---- GND (DCF77)
                                            |                  +----------------------- GND (TEMT6000)
                                            +------------------------------------------ VSS (I2C: RV-8263, SHT31)

    GPIO23 (SDA) ---------------------------+------------------ SDA (RV-8263)
                                            |
                                            +------------------ SDA (SHT31)

    GPIO22 (SCL) ---------------------------+------------------ SCL (RV-8263)
                                            |
                                            +------------------ SCL (SHT31)

    GPIO36 (ADC) ------------------------------------------------ AO/OUT (TEMT6000)

    GPIO13 -------------------------------------------------------- DATA/OUT (DCF77)

    GPIO19 (SPI SCK) ------------------------------------------------ CLK (MAX7219)

    GPIO18 (SPI MOSI) ----------------------------------------------- DIN (MAX7219)

    GPIO5  (SPI CS) ------------------------------------------------- CS  (MAX7219)


Pinbelegung im Code
-------------------

- I2C SDA: GPIO23
- I2C SCL: GPIO22
- TEMT6000 ADC: GPIO36
- DCF77 Signal: GPIO13
- MAX7219 CLK (SCK): GPIO19
- MAX7219 DIN (MOSI): GPIO18
- MAX7219 CS: GPIO5


Hinweis DCF77 Versorgung
------------------------

- DCF77 darf hier mit 5V versorgt werden (wie von dir gewuenscht).
- Wichtig: Das DCF77-Datensignal muss auf 3.3V-Pegel zum ESP32 angepasst werden (Spannungsteiler, Pegelwandler oder Open-Collector mit 3.3V Pull-up).
- Fuer Signalqualitaet kann 5V beim DCF-Empfaenger etwas robuster sein.
- Wenn dein Modul sauber mit 3.3V laeuft, ist das oft die einfachste und sicherste Loesung, weil dann meist kein Pegelwandler noetig ist.


ASCII-Boardplan DIN-Lochraster 32x54 (einseitig)
-------------------------------------------------

Unten ist ein Rasterplan mit 32 Reihen und 54 Spalten.
Empfehlung fuer einseitige Platinen: Schienen horizontal fuehren, Signale vertikal mit Drahtbruecken.

        +----------------------------------------------------+
        |5V==================================================|
        |....................................................|
        |3V3=================================================|
        |....................................................|
        |GND=================================================|
        |....................................................|
        |SDA=================================================|
        |SCL=================================================|
        |....................................................|
        |..........ESP32 NodeMCU Sockel 2x19 (oben->unten)...|
        |L01 3V3   o......................o GND    R01       |
        |L02 RESET o......................o GPIO23 R02       |
        |L03 GPIO36o......................o GPIO22 R03       |
        |L04 GPIO39o......................o INT    R04       |
        |L05 GPIO34o......................o INT    R05       |
        |L06 GPIO35o......................o GPIO21 R06       |
        |L07 GPIO32o......................o GND    R07       |
        |L08 GPIO33o......................o GPIO19 R08       |
        |L09 GPIO25o......................o GPIO18 R09       |
        |L10 GPIO26o......................o GPIO5  R10       |
        |L11 GPIO27o......................o GPIO17 R11       |
        |L12 GPIO14o......................o GPIO16 R12       |
        |L13 GPIO12o......................o GPIO4  R13       |
        |L14 GND   o......................o GPIO0  R14       |
        |L15 GPIO13o......................o GPIO2  R15       |
        |L16 INT   o......................o GPIO15 R16       |
        |L17 INT   o......................o INT    R17       |
        |L18 INT   o......................o INT    R18       |
        |L19 5V    o......................o INT    R19       |
        |....................................................|
        +----------------------------------------------------+

Empfohlene Belegung auf dem Plan
--------------------------------

- Schienen:
    5V in Reihe 1, 3V3 in Reihe 3, GND in Reihe 5, SDA in Reihe 7, SCL in Reihe 8
- Rechte Pinreihe NodeMCU (R):
    R02=GPIO23 -> SDA-Schiene, R03=GPIO22 -> SCL-Schiene
    R08=GPIO19 -> MAX7219 CLK
    R09=GPIO18 -> MAX7219 DIN
    R10=GPIO5  -> MAX7219 CS
- Linke Pinreihe NodeMCU (L):
    L03=GPIO36 -> TEMT6000 AO
    L15=GPIO13 -> DCF77 DATA
- Versorgungen zu den Modulen:
    RV-8263 + SHT31 an 3V3/GND + SDA/SCL
    TEMT6000 an 3V3/GND + GPIO36
    MAX7219 an 3V3/GND + GPIO19/GPIO18/GPIO5
    DCF77 an 5V/GND + GPIO13 (Signal auf 3.3V-Pegel anpassen)



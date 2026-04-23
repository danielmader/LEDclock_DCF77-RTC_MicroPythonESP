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


* R1 = R2: 10 kOhm
* D1 = D2: Schottky-Diode BAT 42/43 oder BAT 86


Schaltoption für Display (nachts aus)
-------------------------------------

                    +3V3
                    |
                    |      Q1 (P-MOSFET, z.B. AO3407A)
                    +------S
                            |
    ESP_GPIO ---- R1 220 ---G
                            |
                            +---- R2 100k ---- GND
                            |
                            D-------------------------> VCC_BAUTEIL (geschaltete 3,3V)

    GND ESP ------------------------------------------> GND_BAUTEIL


* Q1: AO3407A (P-Kanal MOSFET, SOT-23)
* R1: 220 Ohm (GPIO zu Gate)
* R2: 100 kOhm (Gate nach GND, sorgt für Default EIN)

Variante 2 für Schaltoption (sichere Pegel mit 3.3V-GPIO)
---------------------------------------------------------

                    +5V
                    |
                    |        Q1 P-MOSFET (z.B. AO3407A)
                    +--------S
                                |
                                D-----------------------> +V_BAUTEIL (geschaltete 5V)
                                |
                                G----R5 220----+
                                |              |
                            R1 100k         C
                                |             Q3 PNP (z.B. BC857, SOT-23)
                            GND             E
                                            |
                                            +5V
                                            |
                                R2 47k       |
    +5V -------------------------/\/\/\---------+---- B (Q3)
                                                |
                                                C
                                            Q2 NPN (z.B. BC847, SOT-23)
                                                E
                                                |
                                                GND

    ESP_GPIO ---- R3 10k ---- B (Q2)
                        |
                    R4 100k
                        |
                    GND

    GND ESP ------------------------------------------ GND_BAUTEIL

* R1 = 100k, zieht Gate von Q1 nach GND, dadurch Default EIN.
* R2 = 47k, zieht Basis von Q3 nach +5V, hält Q3 im Default AUS.
* R3 = 10k, Basiswiderstand für Q2 vom ESP-GPIO.
* R4 = 100k, hält Q2 sicher AUS bei schwebendem GPIO.
* R5 = 220 Ohm, Gate-Serienwiderstand für Q1.

### Funktionsweise

Default beim Boot (GPIO hochohmig): Q2 AUS, Q3 AUS, Q1-Gate wird über R1 auf GND gezogen, Q1 EIN, Bauteil versorgt.
GPIO Low: gleiches Verhalten, bleibt EIN.
GPIO High 3,3V: Q2 EIN, zieht Q3-Basis nach GND, Q3 EIN, Q1-Gate wird auf +5V gezogen, Q1 AUS, Bauteil stromlos.

### Warum sichere Pegel

ESP-Pin hängt nur an der Basis von Q2 über R3, bekommt keine 5V zurück.
Die 5V-Umschaltung passiert in der Transistorstufe Q2/Q3 und am Gate von Q1.
Damit ist die Pegelanpassung elektrisch sauber und robust.

### Praktische Hinweise

Direkt am Bauteil 100 nF zwischen +V_BAUTEIL und GND.
Falls Last größer ist: zusätzlich 10 µF am geschalteten Ausgang.
Einen GPIO nehmen, der beim Boot nicht kurz aktiv high wird.

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

Schienen horizontal, Signale vertikal mit Drahtbruecken.

        +----------------------------------------------------+
    01  |5V==================================================|
        |....................................................|
        |3V3=================================================|
        |....................................................|
    05  |GND=================================================|
        |....................................................|
        |SDA=================================================|
        |SCL=================================================|
        |....................................................|
    10  |...................ESP32 NodeMCU....................|
        |   L01 3V3    o......................o GND    R01   |
        |   L02 RESET  o......................o GPIO23 R02   |
        |   L03 GPIO36 o......................o GPIO22 R03   |
        |   L04 GPIO39 o......................o INT    R04   |
    15  |   L05 GPIO34 o......................o INT    R05   |
        |   L06 GPIO35 o......................o GPIO21 R06   |
        |   L07 GPIO32 o......................o GND    R07   |
        |   L08 GPIO33 o......................o GPIO19 R08   |
        |   L09 GPIO25 o......................o GPIO18 R09   |
    20  |   L10 GPIO26 o......................o GPIO5  R10   |
        |   L11 GPIO27 o......................o GPIO17 R11   |
        |   L12 GPIO14 o......................o GPIO16 R12   |
        |   L13 GPIO12 o......................o GPIO4  R13   |
        |   L14 GND    o......................o GPIO0  R14   |
    25  |   L15 GPIO13 o......................o GPIO2  R15   |
        |   L16 INT    o......................o GPIO15 R16   |
        |   L17 INT    o......................o INT    R17   |
        |   L18 INT    o......................o INT    R18   |
        |   L19 5V     o......................o INT    R19   |
    30  |....................................................|
        |....................................................|
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

Pinouts
-------

### RV-8263
* NC
* Vss
* NC (CLKOE)
* NC (INT)
* VDD
* NC (CLKOUT)
* SCL
* SDA

### SHT31
* VING
* GND
* SCL
* SDA

### TEMT6000
* OUT
* GND
* VCC

### DCF77
* VIN
* SIG
* GND

### MAX7219
* VCC
* GND
* DIN
* CS
* CLK

"""Lädt die boardspezifische Pinbelegung aus einer JSON-Datei.

Auswahl der Konfigurationsdatei:
1. Existiert eine Datei 'board.json' im Dateisystem, wird diese verwendet
   (manuelles Override, z.B. für Sonderaufbauten).
2. Ansonsten wird das Board automatisch über os.uname().machine erkannt
   und die passende Datei geladen:
   * ESP32-S3  -> board_esp32-s3-wroom-1.json
   * ESP32     -> board_esp-wroom-32.json

Es genügt also, beide JSON-Dateien zusammen mit den Skripten auf das
Board zu kopieren - die richtige wird beim Start automatisch gewählt.
"""

import json
import os

import machine

## Zuordnung: Erkennungsmuster in os.uname().machine -> Konfigurationsdatei
## Wichtig: "ESP32S3" muss VOR "ESP32" geprüft werden (Teilstring!)
_BOARD_FILES = (
    ("ESP32S3", "board_esp32-s3-wroom-1.json"),
    ("ESP32", "board_esp-wroom-32.json"),
)

## Manuelles Override: Wenn diese Datei existiert, wird sie bevorzugt geladen
_OVERRIDE_FILE = "board.json"

## Modulweiter Cache, damit die Datei nur einmal gelesen wird
_config = None


##------------------------------------------------------------------------------
def _find_config_file() -> str:
    """Ermittelt den Dateinamen der zu ladenden Board-Konfiguration.

    Returns
    -------
    * str: Dateiname der JSON-Konfiguration
    """
    ## 1) Manuelles Override
    try:
        os.stat(_OVERRIDE_FILE)
        return _OVERRIDE_FILE
    except OSError:
        pass

    ## 2) Automatische Board-Erkennung, z.B.
    ##    'ESP32 module with ESP32' oder
    ##    'Generic ESP32S3 module with octal SPIRAM with ESP32S3'
    machine_name = os.uname().machine.upper().replace("-", "").replace("_", "")
    for pattern, filename in _BOARD_FILES:
        if pattern in machine_name:
            return filename

    raise RuntimeError(f"Board nicht erkannt: {os.uname().machine}")


##------------------------------------------------------------------------------
def load() -> dict:
    """Lädt die Board-Konfiguration (mit Cache).

    Returns
    -------
    * dict: Konfigurations-Dictionary aus der JSON-Datei
    """
    global _config
    if _config is None:
        filename = _find_config_file()
        with open(filename) as f:
            _config = json.load(f)
        print(f"[BOARDCONFIG] '{filename}' geladen (Board: {_config.get('board')})")
    return _config


##------------------------------------------------------------------------------
def get_i2c() -> machine.I2C:
    """Erzeugt den konfigurierten I2C-Bus (SHT31 & RV-8263).

    Mit externen 10k-Widerständen kann 'pull=None' gesetzt werden, ansonsten
    ist der interne Pull-up hilfreich => zur Sicherheit interne Pull-ups an.
    freq=100000 (100kHz) ist sehr stabil für RTCs
    => Reduziere auf 50kHz, um Störung des DCF77-Empfangs zu minimieren.

    Returns
    -------
    * machine.I2C: Initialisierter I2C-Bus
    """
    cfg = load()["i2c"]
    sda_pin = machine.Pin(cfg["sda"], machine.Pin.IN, machine.Pin.PULL_UP)
    scl_pin = machine.Pin(cfg["scl"], machine.Pin.IN, machine.Pin.PULL_UP)
    return machine.I2C(cfg["id"], scl=scl_pin, sda=sda_pin, freq=cfg["freq"])


##------------------------------------------------------------------------------
def get_spi() -> machine.SPI:
    """Erzeugt den konfigurierten SPI-Bus (MAX7219 LED-Matrix).

    Baudraten-Empfehlung (Key 'baudrate' in der JSON-Datei):
    * 500 kHz für maximale Stabilität bei langen Kabeln oder vielen Modulen
    * 1 MHz für flüssigere Darstellung
    * 10 MHz für maximale Performance (nur bei sehr kurzen Kabeln stabil)

    Returns
    -------
    * machine.SPI: Initialisierter SPI-Bus
    """
    cfg = load()["spi"]
    return machine.SPI(
        cfg["id"],
        baudrate=cfg["baudrate"],
        polarity=0,
        phase=0,
        sck=machine.Pin(cfg["sck"]),
        mosi=machine.Pin(cfg["mosi"]),
    )


##------------------------------------------------------------------------------
def get_spi_cs() -> machine.Pin:
    """Erzeugt den Chip-Select-Pin des SPI-Busses.

    Returns
    -------
    * machine.Pin: CS-Pin als Ausgang
    """
    return machine.Pin(load()["spi"]["cs"], machine.Pin.OUT)


##------------------------------------------------------------------------------
def get_adc_pin() -> machine.Pin:
    """Erzeugt den ADC-Pin des TEMT6000-Helligkeitssensors.

    Returns
    -------
    * machine.Pin: ADC-fähiger Pin
    """
    return machine.Pin(load()["pins"]["temt6000_adc"])


##------------------------------------------------------------------------------
def get_dcf_pin() -> machine.Pin:
    """Erzeugt den Daten-Pin des DCF77-Empfängers.

    Returns
    -------
    * machine.Pin: Eingang mit Pull-up
    """
    return machine.Pin(load()["pins"]["dcf77_data"], machine.Pin.IN, machine.Pin.PULL_UP)


##------------------------------------------------------------------------------
def get_display_power_pin() -> "machine.Pin | None":
    """Erzeugt den Power-Control-Pin der LED-Matrix (optional).

    Returns
    -------
    * machine.Pin | None: Ausgang oder None, wenn nicht beschaltet (null in JSON)
    """
    pin_no = load()["pins"]["display_power"]
    return None if pin_no is None else machine.Pin(pin_no, machine.Pin.OUT)


##------------------------------------------------------------------------------
def get_status_led_pin() -> "machine.Pin | None":
    """Erzeugt den Pin der Status-LED (optional).

    Returns
    -------
    * machine.Pin | None: Ausgang oder None, wenn nicht vorhanden (null in JSON)
    """
    pin_no = load()["pins"]["status_led"]
    return None if pin_no is None else machine.Pin(pin_no, machine.Pin.OUT)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":
    cfg = load()
    print("Board:", cfg["board"])
    print("I2C:  ", cfg["i2c"])
    print("SPI:  ", cfg["spi"])
    print("Pins: ", cfg["pins"])

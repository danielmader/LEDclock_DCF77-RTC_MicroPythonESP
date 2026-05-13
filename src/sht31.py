import time

import machine


##==============================================================================
class SHT31:
    ## Standard-I2C-Adresse der SHT31
    SHT31_ADDR = 0x44

    ##--------------------------------------------------------------------------
    def __init__(self, i2c: machine.I2C) -> None:
        """Initialisiert den SHT31-Sensortreiber.

        Parameter
        ---------
        * i2c: Initialisierter I2C-Bus

        Returns
        -------
        * None
        """
        self.i2c = i2c
        if not self.scan_bus():
            raise Exception(f"T-H-Sensor 'SHT31' nicht gefunden auf Adresse {hex(self.SHT31_ADDR)}")

    ##--------------------------------------------------------------------------
    def scan_bus(self) -> bool:
        """Prüft, ob der Sensor auf dem I2C-Bus vorhanden ist.

        Returns
        -------
        * bool: True, wenn die SHT31-Adresse gefunden wurde
        """
        # print("Scanne I²C Bus...")
        devices = self.i2c.scan()
        if not devices:
            print("Fehler: Keine I²C-Geräte gefunden! Verkabelung prüfen.")
            return False
        # print(f"Gefundene Geräte: {[hex(d) for d in devices]}")
        return self.SHT31_ADDR in devices

    ##--------------------------------------------------------------------------
    def get_measurement(self) -> tuple:
        """Liest Temperatur und relative Luftfeuchtigkeit.

        Returns
        -------
        * tuple: (temperature_c, humidity_percent) oder (None, None) bei Fehler
        """
        try:
            ## Befehl "High Repeatability" senden (0x2C 0x06)
            self.i2c.writeto(self.SHT31_ADDR, b'\x2c\x06')

            ## Dem Sensor Zeit zum Messen geben (ca. 20ms)
            time.sleep(0.05)

            ## 6 Bytes lesen: [Temp MSB, Temp LSB, CRC, Hum MSB, Hum LSB, CRC]
            data = self.i2c.readfrom(self.SHT31_ADDR, 6)

            ## Temperatur berechnen
            temp_raw = (data[0] << 8) | data[1]
            temperature = -45 + (175 * temp_raw / 65535.0)

            ## Luftfeuchtigkeit berechnen
            hum_raw = (data[3] << 8) | data[4]
            humidity = 100 * hum_raw / 65535.0

            return temperature, humidity
        except Exception as e:
            print("Fehler beim Lesen des SHT31:", e)
            return None, None


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## I2C-Bus-Initialisierung mit expliziten Pin-Definitionen für die ESP32-Standard-Pins SCL=22 SDA=23 und Pull-ups.
    ## Mit externen 10k-Widerständen kann 'pull=None' gesetzt werden, ansonsten ist der interne Pull-up hilfreich.
    ## => Zur Sicherheit interne Pull-ups zusätzlich an.
    sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
    scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
    ## freq=100000 (100kHz) ist sehr stabil für RTCs
    ## => Reduziere auf 50kHz, um Störung des DCF77-Empfangs zu minimieren
    i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=50000)

    print("Lese SHT31 Sensor...")
    sht = SHT31(i2c)
    for _ in range(5):
        t, h = sht.get_measurement()
        if t is not None:
            print(f"Temperatur: {t:.2f} °C | Feuchte: {h:.2f} %rF")
        time.sleep(2)

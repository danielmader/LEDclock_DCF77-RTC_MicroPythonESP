import time

import machine


##==============================================================================
class TEMT6000:
    ##--------------------------------------------------------------------------
    def __init__(self, pin: machine.Pin) -> None:
        """Initialisiert den ADC-Eingang für den TEMT6000.

        Parameter
        ---------
        * adc_pin: GPIO mit ADC-Funktion

        Returns
        -------
        * None
        """
        ## ADC initialisieren
        self.adc = machine.ADC(pin)
        ## ADC.ATTN_11DB ermöglicht den vollen Messbereich bis ca. 3.1-3.3V
        self.adc.init(atten=machine.ADC.ATTN_11DB)

    ##--------------------------------------------------------------------------
    def get_measurement(self) -> tuple:
        """Liest Helligkeit als Rohwert und Prozentwert.

        Returns
        -------
        * tuple: (adc_raw_0_65535, percentage_0_100)
        """
        ## ADC-Rohwert lesen (0 - 65535); read_u16() ist die portable API,
        ## die auf ESP32 wie ESP32-S3 identisch funktioniert (read() ist deprecated)
        raw_value = self.adc.read_u16()
        ## In Prozent umrechnen
        percentage = (raw_value / 65535) * 100
        return raw_value, percentage


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    import boardconfig

    print("Lese TEMT6000 Sensor...")
    adc_pin = boardconfig.get_adc_pin()
    sensor = TEMT6000(adc_pin)
    while True:
        try:
            val, perc = sensor.get_measurement()
            if val is not None:
                print(f"Helligkeit Rohwert: {val:5d} | Intensität: {perc:5.1f}%")
                ## Ein kleiner Balken zur Visualisierung
                bar = "#" * int(perc / 5)
                print(f"[{bar:20s}]")
            time.sleep(1)
        except KeyboardInterrupt:
            print("Messung beendet.")

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
        * tuple: (adc_raw_0_4095, percentage_0_100)
        """
        ## ADC-Rohwert lesen (0 - 4095)
        raw_value = self.adc.read()
        ## In Prozent umrechnen
        percentage = (raw_value / 4095) * 100
        return raw_value, percentage


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    print("Lese TEMT6000 Sensor...")
    adc_pin = machine.Pin(36)
    sensor = TEMT6000(adc_pin)
    while True:
        try:
            val, perc = sensor.get_measurement()
            if val is not None:
                print(f"Helligkeit Rohwert: {val:4d} | Intensität: {perc:5.1f}%")
                ## Ein kleiner Balken zur Visualisierung
                bar = "#" * int(perc / 5)
                print(f"[{bar:20s}]")
            time.sleep(1)
        except KeyboardInterrupt:
            print("Messung beendet.")

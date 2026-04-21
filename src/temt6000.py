import time

import machine  # type: ignore


##==============================================================================
class TEMT6000:
    ##--------------------------------------------------------------------------
    def __init__(self, adc_pin=36):
        ## ADC initialisieren
        self.adc = machine.ADC(machine.Pin(adc_pin))
        ## ADC.ATTN_11DB ermöglicht den vollen Messbereich bis ca. 3.1-3.3V
        self.adc.atten(machine.ADC.ATTN_11DB)

    ##--------------------------------------------------------------------------
    def get_measurement(self):
        ## ADC-Rohwert lesen (0 - 4095)
        raw_value = self.adc.read()
        ## In Prozent umrechnen
        percentage = (raw_value / 4095) * 100
        return raw_value, percentage


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    print("Lese TEMT6000 Sensor...")
    sensor = TEMT6000()
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

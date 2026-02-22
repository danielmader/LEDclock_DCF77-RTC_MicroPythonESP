from machine import ADC, Pin
import time

# ADC initialisieren an GPIO 34
# ADC.ATTN_11DB ermöglicht den vollen Messbereich bis ca. 3.1V - 3.3V
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)

def read_light():
    # Rohwert lesen (0 - 4095)
    raw_value = adc.read()

    # In Prozent umrechnen (grob)
    percentage = (raw_value / 4095) * 100

    return raw_value, percentage

print("Lichtsensor-Test startet (TEMT6000)...")

try:
    while True:
        val, perc = read_light()
        print(f"Helligkeit Rohwert: {val:4d} | Intensität: {perc:5.1f}%")

        # Ein kleiner Balken zur Visualisierung
        bar = "#" * int(perc / 5)
        print(f"[{bar:20s}]")

        time.sleep(0.5)
except KeyboardInterrupt:
    print("Messung beendet.")

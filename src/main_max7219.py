import time
import max7219
from machine import Pin, SPI

## SPI Konfiguration (Beispiel für ESP32)
## Für Pico: spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
spi = SPI(1, baudrate=10000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
cs = Pin(5, Pin.OUT)

## 4 Module à 8x8 Pixel = 32 Breite, 8 Höhe
display = max7219.Matrix8x8(spi, cs, 4)

## Helligkeit einstellen (0 bis 15)
display.brightness(0)

def demo():
    ## 1. Display löschen
    display.fill(0)
    display.show()
    time.sleep(1)

    ## 2. Text schreiben
    display.text('Hi!', 0, 0, 1)
    display.show()
    time.sleep(2)

    ## 3. Lauftext-Animation
    message = "BerryBase rockt!"
    ## Kalkuliere die Länge des Textes (pro Zeichen ca. 8 Pixel)
    for x in range(32, -len(message) * 8, -1):
        display.fill(0)
        display.text(message, x, 0, 1)
        display.show()
        time.sleep(0.05)

# while True:
#     demo()
for _ in range(3):
    demo()

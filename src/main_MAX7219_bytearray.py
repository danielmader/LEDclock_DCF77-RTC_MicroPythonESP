import time
import machine

import max7219


## SPI Konfiguration (Beispiel für ESP32)
## Für Pico: spi = machine.SPI(0, baudrate=10000000, polarity=0, phase=0, sck=machine.Pin(18), mosi=machine.Pin(19))
spi = machine.SPI(1, baudrate=10000000, polarity=0, phase=0, sck=machine.Pin(18), mosi=machine.Pin(23))
cs = machine.Pin(5, machine.Pin.OUT)

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

while True:
    demo()

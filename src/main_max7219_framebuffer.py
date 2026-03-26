## MAX7219 LED-Matrix Herz-Icon
## Binärdarstellung für ein Herz (1 = LED an, 0 = LED aus)
## 01100110 -> 0x66
## 11111111 -> 0xFF
## ... usw.

import framebuf
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

## Das Icon-Bytearray (8x8), um 90° im Uhrzeigersinn rotiert
HEART = bytearray([0x0C, 0x1E, 0x3E, 0x7C, 0x7C, 0x3E, 0x1E, 0x0C])

def draw_icon(data, x_pos, y_pos):
    ## Erstellt einen temporären Buffer für das 8x8 Icon
    fb = framebuf.FrameBuffer(data, 8, 8, framebuf.MONO_VLSB)
    ## Kopiert (blit) das Icon an die gewünschte Stelle auf dem Hauptdisplay
    display.blit(fb, x_pos, y_pos)
    display.show()

# for _ in range(3):
while True:
    ## Animation: Das Herz wandert über die 4 Module
    display.fill(0)
    for x in range(-8, 33):
        display.fill(0)
        draw_icon(HEART, x, 0)
        time.sleep(0.05)

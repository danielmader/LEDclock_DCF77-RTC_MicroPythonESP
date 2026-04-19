import framebuf
import machine
import time

import max7219


## SPI Konfiguration
spi = machine.SPI(1, baudrate=10000000, polarity=0, phase=0, sck=machine.Pin(19), mosi=machine.Pin(18))
cs = machine.Pin(5, machine.Pin.OUT)

## 4 Module à 8x8 Pixel = 32 Breite, 8 Höhe
display = max7219.Matrix8x8(spi, cs, 4)

## Helligkeit einstellen (0 bis 15)
display.brightness(0)


##==============================================================================
def draw_icon(data, x_pos, y_pos):
    ## Erstellt einen temporären Buffer für das 8x8 Icon
    fb = framebuf.FrameBuffer(data, 8, 8, framebuf.MONO_VLSB)
    ## Kopiert (blit) das Icon an die gewünschte Stelle auf dem Hauptdisplay
    display.blit(fb, x_pos, y_pos)
    display.show()


##==============================================================================
def clear_display():
    display.fill(0)
    display.show()


##==============================================================================
def write_text(text, x, y):
    display.text(text, x, y, 1)
    display.show()


##==============================================================================
def write_scrolling_text(text, y):
    text_length = len(text) * 8  # ca. 8 Pixel pro Zeichen
    for x in range(32, -text_length, -1):
        display.fill(0)
        display.text(text, x, y, 1)
        display.show()
        time.sleep(0.05)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## MAX7219 LED-Matrix Herz-Icon
    ## Binärdarstellung für ein Herz (1 = LED an, 0 = LED aus)
    ## 01100110 -> 0x66
    ## 11111111 -> 0xFF
    ## ... usw.
    ## Icon-Bytearray (8x8), um 90° im Uhrzeigersinn rotiert
    HEART = bytearray([0x0C, 0x1E, 0x3E, 0x7C, 0x7C, 0x3E, 0x1E, 0x0C])

    while True:
        ## 1) Animation: Das Herz wandert über die 4 Module
        display.fill(0)
        for x in range(-8, 33):
            display.fill(0)
            draw_icon(HEART, x, 0)
            time.sleep(0.05)

        ## 2) Demo-Text und Lauftext
        write_text("MAX7219", 0, 0)
        time.sleep(1)
        write_scrolling_text("Hello World!", 0)
        time.sleep(1)
        write_scrolling_text("ESP32 & MicroPython", 0)
        time.sleep(2)

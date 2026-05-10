import time

import framebuf  # type: ignore
import machine  # type: ignore
import max7219  # type: ignore

from characters import FONT_3X5, FONT_5x7

## SPI Konfiguration
spi = machine.SPI(1, baudrate=10000000, polarity=0, phase=0, sck=machine.Pin(5), mosi=machine.Pin(19))
cs = machine.Pin(18, machine.Pin.OUT)

## Power-Supply für MAX7219 (optional, abhängig von der Verkabelung)
# power_pin = machine.Pin(0, machine.Pin.OUT)
# power_pin.value(1)  # MAX7219 mit Strom versorgen (HIGH = an, LOW = aus)
## GPIO0 ist ein Boot-Strapping-Pin am ESP32.
## Daher ist die Versorgungsschaltung per GPIO standardmäßig AUS.
USE_GPIO_POWER_SWITCH = False
if USE_GPIO_POWER_SWITCH:
    power_pin = machine.Pin(0, machine.Pin.OUT)
    power_pin.value(1)  # HIGH = an, LOW = aus
    time.sleep_ms(20)   # kurze Stabilisierung nach dem Einschalten

## 4 Module à 8x8 Pixel = 32 Breite, 8 Höhe
display = max7219.Matrix8x8(spi, cs, 4)

## Helligkeit einstellen (0 bis 15)
display.brightness(0)
display.fill(0)
display.show()


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
def _draw_glyph(ch, x, y, font_dict):
    """Generalisierte Glyphen-Zeichnungsfunktion für beliebige Fontgrößen.

    Args:
        ch: Das zu zeichnende Zeichen
        x, y: Position auf dem Display
        font_dict: Font-Dictionary mit "_meta_" und Glyph-Einträgen
                   Format: {"_meta_": {"width": w, "height": h}, "A": (...), ...}
    """
    meta = font_dict.get("_meta_", {})
    width = meta.get("width", 3)
    height = meta.get("height", 5)

    glyph = font_dict.get(ch, font_dict.get(" ", None))
    if glyph is None or glyph == font_dict.get("_meta_"):
        return

    for row in range(min(height, len(glyph))):
        bits = glyph[row]
        for col in range(width):
            if bits & (1 << (width - 1 - col)):
                display.pixel(x + col, y + row, 1)


##==============================================================================
def write_text(text, x, y, font_dict="builtin"):
    """Schreibt Text mit dem angegebenen Font.

    Args:
        text: Der zu schreibende Text
        x, y: Startposition
        font_dict: Font-Dictionary oder "builtin" für FrameBuffer-Standardfont (default: "builtin")
                   Beispiele: FONT_3X5, FONT_5x7, oder "builtin"
    """
    # FrameBuffer-Standardfont verwenden
    if font_dict is None or font_dict == "builtin":
        display.text(text, x, y, 1)
        display.show()
        return

    # Custom Font verwenden
    meta = font_dict.get("_meta_", {})
    char_width = meta.get("width", 3)
    spacing = 1  # 1 Pixel Abstand zwischen Zeichen

    x_pos = x
    for ch in text.upper():
        _draw_glyph(ch, x_pos, y, font_dict)
        x_pos += char_width + spacing
    display.show()


##==============================================================================
def write_scrolling_text(text, y, font_dict="builtin", speed_s=0.05):
    """Scrollt Text mit dem angegebenen Font über die Matrix.

    Args:
        text: Der zu scrollende Text
        y: Y-Position
        font_dict: Font-Dictionary oder "builtin" für FrameBuffer-Standardfont (default: "builtin")
                   Beispiele: FONT_3X5, FONT_5x7, oder "builtin"
        speed_s: Verzögerung zwischen Frames in Sekunden
    """
    # FrameBuffer-Standardfont verwenden
    if font_dict is None or font_dict == "builtin":
        text_length = len(text) * 8  # ca. 8 Pixel pro Zeichen im Standardfont
        for x in range(32, -text_length, -1):
            display.fill(0)
            display.text(text, x, y, 1)
            display.show()
            time.sleep(speed_s)
        return

    # Custom Font verwenden
    meta = font_dict.get("_meta_", {})
    char_width = meta.get("width", 3)
    spacing = 1
    text_upper = text.upper()
    text_length = len(text_upper) * (char_width + spacing)

    for x in range(32, -text_length, -1):
        display.fill(0)
        write_text(text_upper, x, y, font_dict)
        time.sleep(speed_s)


##==============================================================================
# Aliase für häufig verwendete Fonts
def write_text_compact(text, x, y):
    """Schreibt Text in kompakter 3x5-Schrift."""
    write_text(text, x, y, FONT_3X5)

def write_scrolling_text_compact(text, y, speed_s=0.05):
    """Scrollt Text in kompakter 3x5-Schrift."""
    write_scrolling_text(text, y, FONT_3X5, speed_s)

def write_text_builtin(text, x, y):
    """Schreibt Text im FrameBuffer-Standardfont (fett/breit)."""
    write_text(text, x, y, "builtin")

def write_scrolling_text_builtin(text, y, speed_s=0.05):
    """Scrollt Text im FrameBuffer-Standardfont (fett/breit)."""
    write_scrolling_text(text, y, "builtin", speed_s)


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

        ## 2) Demo-Text mit FrameBuffer-Standardfont (fett/breit)
        display.fill(0)
        write_text("MAX7219", 0, 1)
        time.sleep(1)
        write_scrolling_text("Hello World!", 1)
        time.sleep(1)
        write_scrolling_text("ESP32 & MicroPython", 1)
        time.sleep(2)

        ## 3) Demo-Text mit kompakter 3x5-Schrift (dünn/schmal)
        display.fill(0)
        write_text_compact("MAX7219", 0, 1)
        time.sleep(1)
        write_scrolling_text_compact("Hello World!", 1)
        time.sleep(1)
        write_scrolling_text_compact("ESP32 & MicroPython", 1)
        time.sleep(1)

        ## 4) Testsequenz für Sonderzeichen der kompakten Schrift
        write_scrolling_text_compact(":,.°%-_#+*/|=", 1)
        time.sleep(2)

        ## 5) Demo mit FONT_5x7 (größere Ziffern für Uhranzeige)
        display.fill(0)
        write_text("12:45", 0, 0, FONT_5x7)
        time.sleep(2)

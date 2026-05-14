import time

import framebuf
import machine
import max7219

from characters import FONT_3X5, FONT_5X7

## SPI Konfiguration
baudrate = 10000000  # 10 MHz, abhängig von der Verkabelung und Qualität der Verbindung
baudrate = 1000000  # 1 MHz für stabilere Verbindung bei längeren Kabeln oder mehreren Modulen
baudrate = 500000  # 500 kHz für maximale Stabilität bei langen Kabeln oder vielen Modulen
spi = machine.SPI(1, baudrate=baudrate, polarity=0, phase=0, sck=machine.Pin(5), mosi=machine.Pin(19))
cs = machine.Pin(18, machine.Pin.OUT)

## 4 Module à 8x8 Pixel = 32 x 8 (BxH)
# self.display = max7219.Matrix8x8(self.spi, self.cs, self.num_modules)
# self.display.brightness(self.brightness_level)
# self.display.fill(0)
# self.display.show()

## Power-Supply-Schaltung
power_pin = machine.Pin(0, machine.Pin.OUT)


##==============================================================================
class Max7219Matrix(max7219.Matrix8x8):
    def __init__(
        self,
        spi: machine.SPI,
        cs: machine.Pin,
        num_modules: int = 4,
        modules_per_row: "int | None" = None,
        power_pin: "machine.Pin | None" = None,
        brightness_level: int = 8,  # Standard-Helligkeit (0-15)
        **kwargs,
    ) -> None:
        """Initialisiert die MAX7219-Matrix.

        Parameter
        ---------
        * spi: Konfiguriertes SPI-Objekt
        * cs: Chip-Select-Pin
        * num_modules: Anzahl kaskadierter 8x8-Module
        * modules_per_row: Anzahl Module pro physischer Zeile; Standard ist alle Module in einer Zeile
        * power_pin: Optionaler GPIO zum Schalten der Versorgung
        * brightness_level: Helligkeit des Displays (0-15)

        Returns
        -------
        * None
        """
        self.spi = spi
        self.cs = cs
        self.num_modules = num_modules
        self.modules_per_row = num_modules if modules_per_row is None else modules_per_row

        if self.modules_per_row <= 0 or self.num_modules % self.modules_per_row != 0:
            raise ValueError("modules_per_row muss ein positiver Teiler von num_modules sein")

        self.power_pin = power_pin
        self.brightness_level = brightness_level  # Standard-Helligkeit (0-15)

        ## optionale Power-Supply-Schaltung
        if self.power_pin is not None:
            self.power_pin.value(1)  # HIGH = an, LOW = aus
            time.sleep_ms(20)  # kurze Stabilisierung nach dem Einschalten

        super().__init__(self.spi, self.cs, self.num_modules)

        ## Helligkeit einstellen (0 bis 15)
        self.brightness(self.brightness_level)
        self.clear()
        self.show()

    ##--------------------------------------------------------------------------
    def get_row_width(self) -> int:
        """Gibt die Breite einer physischen Display-Zeile in Pixeln zurück.

        Returns
        -------
        * int: Zeilenbreite in Pixeln
        """
        return self.modules_per_row * 8

    ##--------------------------------------------------------------------------
    def get_row_x_offset(self, row: int = 0) -> int:
        """Gibt den X-Offset einer physischen Display-Zeile zurück.

        Parameter
        ---------
        * row: Physische Zeile, beginnend bei 0

        Returns
        -------
        * int: X-Offset der Zeile in Pixeln
        """
        row_count = self.num_modules // self.modules_per_row
        if not (0 <= row < row_count):
            raise ValueError("row liegt außerhalb der konfigurierten Display-Zeilen")
        return row * self.get_row_width()

    ##--------------------------------------------------------------------------
    def draw_icon(self, data: bytearray, x_pos: int, y_pos: int) -> None:
        """Zeichnet ein 8x8-Icon an der angegebenen Position.

        Parameter
        ---------
        * data: 8x8-Monobitmap im MONO_VLSB-Format
        * x_pos: Ziel-X-Position
        * y_pos: Ziel-Y-Position

        Returns
        -------
        * None
        """
        ## Erstellt einen temporären Buffer für das 8x8 Icon
        fb = framebuf.FrameBuffer(data, 8, 8, framebuf.MONO_VLSB)
        ## Kopiert (blit) das Icon an die gewünschte Stelle auf dem Hauptdisplay
        self.blit(fb, x_pos, y_pos)
        # self.show()

    ##--------------------------------------------------------------------------
    def clear_display(self) -> None:
        """Löscht den Display-Inhalt.

        Returns
        -------
        * None
        """
        self.fill(0)
        # self.show()

    def clear(self) -> None:
        """Alias für clear_display()."""
        self.clear_display()

    ##--------------------------------------------------------------------------
    def _draw_glyph(self, ch: str, x: int, y: int, font_dict: "dict | str | None") -> None:
        """
        Generalisierte Glyphen-Zeichnungsfunktion für beliebige Fontgrößen.

        Parameter
        ---------
        * ch: Das zu zeichnende Zeichen
        * x: X-Position auf dem Display
        * y: Y-Position auf dem Display
        * font_dict: Font-Dictionary mit "_meta_" und Glyph-Einträgen
            Format: {"_meta_": {"width": w, "height": h}, "A": (...), ...}

        Returns
        -------
        * None
        """
        if not isinstance(font_dict, dict):
            return

        meta = font_dict.get("_meta_", {})
        height = meta.get("height", 5)

        glyph = font_dict.get(ch, font_dict.get(" ", None))
        if glyph is None or glyph == font_dict.get("_meta_"):
            return

        min_bit, _, span_width = self._get_glyph_bit_span(ch, font_dict)
        if span_width <= 0:
            return

        for row in range(min(height, len(glyph))):
            ## Auf den tatsächlich genutzten Bitbereich normalisieren (proportional)
            bits = glyph[row] >> min_bit
            for col in range(span_width):
                if bits & (1 << (span_width - 1 - col)):
                    self.pixel(x + col, y + row, 1)

    ##--------------------------------------------------------------------------
    @staticmethod
    def _bit_length_fallback(value: int) -> int:
        """MicroPython-kompatible Bitlängen-Berechnung ohne int.bit_length().

        Parameter
        ---------
        * value: Ganzzahlwert

        Returns
        -------
        * int: Anzahl gesetzter Bit-Positionen bis zum höchsten 1-Bit
        """
        bits = 0
        while value:
            bits += 1
            value >>= 1
        return bits

    ##--------------------------------------------------------------------------
    @staticmethod
    def _trailing_zeros_fallback(value: int) -> int:
        """Anzahl nachlaufender Nullen im Binärmuster (LSB-seitig).

        Parameter
        ---------
        * value: Ganzzahlwert

        Returns
        -------
        * int: Anzahl LSB-seitiger 0-Bits
        """
        if value == 0:
            return 0
        zeros = 0
        while (value & 1) == 0:
            zeros += 1
            value >>= 1
        return zeros

    ##--------------------------------------------------------------------------
    def _get_glyph_bit_span(self, ch: str, font_dict: "dict | str | None") -> tuple:
        """Liefert den genutzten Bitbereich einer Glyph.

        Parameter
        ---------
        * ch: Zu analysierendes Zeichen
        * font_dict: Font-Dictionary mit Metadaten und Glyphen

        Returns
        -------
        * tuple: (min_bit, max_bit, span_width)
        """
        if not isinstance(font_dict, dict):
            return 0, 0, 0

        meta = font_dict.get("_meta_", {})
        default_width = meta.get("width", 3)
        space_width = meta.get("space_width", 1)

        glyph = font_dict.get(ch, font_dict.get(" ", None))
        if glyph is None or glyph == font_dict.get("_meta_"):
            return 0, 0, space_width

        min_bit = None
        max_bit = None
        for row_bits in glyph:
            if row_bits > 0:
                row_min = self._trailing_zeros_fallback(row_bits)
                row_max = self._bit_length_fallback(row_bits) - 1
                min_bit = row_min if min_bit is None else min(min_bit, row_min)
                max_bit = row_max if max_bit is None else max(max_bit, row_max)

        if min_bit is None or max_bit is None:
            return 0, 0, space_width

        span_width = (max_bit - min_bit) + 1
        return min_bit, max_bit, min(default_width, span_width)

    ##--------------------------------------------------------------------------
    def _get_glyph_effective_width(self, ch: str, font_dict: "dict | str | None") -> int:
        """Ermittelt die effektive Zeichenbreite aus dem genutzten Bitbereich.

        Parameter
        ---------
        * ch: Zu analysierendes Zeichen
        * font_dict: Font-Dictionary mit Metadaten und Glyphen

        Returns
        -------
        * int: Effektive Breite in Pixeln
        """
        _, _, span_width = self._get_glyph_bit_span(ch, font_dict)
        return span_width

    ##--------------------------------------------------------------------------
    def get_text_width(self, text: str, font_dict: "dict | str | None" = "builtin", spacing: int = 1) -> int:
        """Berechnet die Pixelbreite eines Textes für den gewählten Font.

        Parameter
        ---------
        * text: Eingabetext
        * font_dict: Font-Dictionary oder "builtin"
        * spacing: Zeichenabstand in Pixeln

        Returns
        -------
        * int: Gesamte Textbreite in Pixeln
        """
        if font_dict is None or font_dict == "builtin":
            return len(text) * 8

        text_upper = text.upper()
        if not text_upper:
            return 0

        width = 0
        for ch in text_upper:
            width += self._get_glyph_effective_width(ch, font_dict) + spacing

        ## Letzten Zeichenabstand nicht mitzählen
        return max(0, width - spacing)

    ##--------------------------------------------------------------------------
    def get_centered_x(
        self,
        text: str,
        font_dict: "dict | str | None" = "builtin",
        spacing: int = 1,
        clamp: bool = False,
        row: int = 0,
    ) -> int:
        """Berechnet die zentrierte Start-X-Position für den Text.

        Parameter
        ---------
        * text: Eingabetext
        * font_dict: Font-Dictionary oder "builtin"
        * spacing: Zeichenabstand in Pixeln
        * clamp: Begrenzt negative X-Positionen auf 0
        * row: Physische Display-Zeile, auf der zentriert werden soll

        Returns
        -------
        * int: Startposition für zentriertes Rendering
        """
        display_width = self.get_row_width()
        text_width = self.get_text_width(text, font_dict, spacing)
        x_pos = (display_width - text_width) // 2
        if clamp:
            x_pos = max(0, x_pos)
        return self.get_row_x_offset(row) + x_pos

    ##--------------------------------------------------------------------------
    def write_text_centered(
        self,
        text: str,
        y: int,
        font_dict: "dict | str | None" = "builtin",
        spacing: int = 1,
        clamp: bool = False,
        clear: bool = False,
        row: int = 0,
    ) -> None:
        """Schreibt einen Text horizontal zentriert.

        Parameter
        ---------
        * text: Auszugebender Text
        * y: Ziel-Y-Position
        * font_dict: Font-Dictionary oder "builtin"
        * spacing: Zeichenabstand in Pixeln
        * clamp: Begrenzt negative X-Positionen auf 0
        * clear: Löscht das Display vor dem Schreiben
        * row: Physische Display-Zeile, auf der geschrieben werden soll

        Returns
        -------
        * None
        """
        x_pos = self.get_centered_x(text, font_dict, spacing, clamp, row)
        if clear:
            self.fill(0)
        self.write_text(text, x_pos, y, font_dict, spacing)
        # self.show()

    ##--------------------------------------------------------------------------
    def write_text(self, text: str, x: int, y: int, font_dict: "dict | str | None" = "builtin", spacing: int = 1) -> None:
        """
        Schreibt Text mit dem angegebenen Font.

        Parameter
        ---------
        * text: Der zu schreibende Text
        * x: X-Position
        * y: Y-Position
        * font_dict: Font-Dictionary oder "builtin" für FrameBuffer-Standardfont (default: "builtin")
            Beispiele: FONT_3X5, FONT_5x7, oder "builtin"
        * spacing: Zeichenabstand in Pixeln

        Returns
        -------
        * None
        """
        ## FrameBuffer-Standardfont verwenden
        if font_dict is None or font_dict == "builtin":
            self.text(text, x, y, 1)
        else:
            ## Custom Font verwenden
            x_pos = x
            for ch in text.upper():
                self._draw_glyph(ch, x_pos, y, font_dict)
                x_pos += self._get_glyph_effective_width(ch, font_dict) + spacing
        # self.show()

    ##--------------------------------------------------------------------------
    def write_scrolling_text(
        self,
        text: str,
        y: int,
        font_dict: "dict | str | None" = "builtin",
        speed_s: float = 0.05,
        spacing: int = 1,
    ) -> None:
        """Scrollt Text mit dem angegebenen Font über die Matrix.

        Parameter
        ---------
        * text: Der zu scrollende Text
        * y: Y-Position
        * font_dict: Font-Dictionary oder "builtin" für FrameBuffer-Standardfont (default: "builtin")
                Beispiele: FONT_3X5, FONT_5x7, oder "builtin"
        * speed_s: Verzögerung zwischen Frames in Sekunden
        * spacing: Zeichenabstand in Pixeln

        Returns
        -------
        * None
        """
        ## FrameBuffer-Standardfont verwenden
        if font_dict is None or font_dict == "builtin":
            text_length = len(text) * 8  # ca. 8 Pixel pro Zeichen im Standardfont
            for x in range(32, -text_length, -1):
                self.fill(0)
                self.text(text, x, y, 1)
                self.show()
                time.sleep(speed_s)
        else:
            ## Custom Font verwenden
            text_upper = text.upper()
            text_length = self.get_text_width(text_upper, font_dict, spacing)

            for x in range(32, -text_length, -1):
                self.fill(0)
                self.write_text(text_upper, x, y, font_dict, spacing)
                time.sleep(speed_s)

    ##--- Aliase für häufig verwendete Fonts ----------------------------------
    def write_text_small(self, text: str, x: int, y: int) -> None:
        """Schreibt Text in kleiner 3x5-Schrift.

        Parameter
        ---------
        * text: Auszugebender Text
        * x: Ziel-X-Position
        * y: Ziel-Y-Position

        Returns
        -------
        * None
        """
        self.write_text(text, x, y, FONT_3X5)

    def write_scrolling_text_small(self, text: str, y: int, speed_s: float = 0.05) -> None:
        """Scrollt Text in kleiner 3x5-Schrift.

        Parameter
        ---------
        * text: Auszugebender Text
        * y: Ziel-Y-Position
        * speed_s: Verzögerung zwischen Frames in Sekunden

        Returns
        -------
        * None
        """
        self.write_scrolling_text(text, y, FONT_3X5, speed_s)

    def write_text_compact(self, text: str, x: int, y: int) -> None:
        """Schreibt Text in kompakter 5x7-Schrift.

        Parameter
        ---------
        * text: Auszugebender Text
        * x: Ziel-X-Position
        * y: Ziel-Y-Position

        Returns
        -------
        * None
        """
        self.write_text(text, x, y, FONT_5X7)

    def write_scrolling_text_compact(self, text: str, y: int, speed_s: float = 0.05) -> None:
        """Scrollt Text in kompakter 5x7-Schrift.

        Parameter
        ---------
        * text: Auszugebender Text
        * y: Ziel-Y-Position
        * speed_s: Verzögerung zwischen Frames in Sekunden

        Returns
        -------
        * None
        """
        self.write_scrolling_text(text, y, FONT_5X7, speed_s)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":
    """Beispiel"""
    display = Max7219Matrix(spi, cs, num_modules=4, power_pin=power_pin)

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
            display.draw_icon(HEART, x, 0)
            time.sleep(0.05)

        ## 2) Demo-Text mit FrameBuffer-Standardfont (fett/breit)
        display.fill(0)
        display.write_text("MAX7219", 0, 1)
        time.sleep(1)
        display.write_scrolling_text("Hello World!", 1)
        time.sleep(1)
        display.write_scrolling_text("ESP32 & MicroPython", 1)
        time.sleep(2)

        ## 3a) Demo-Text mit kleiner  3x5-Schrift (dünn/schmal)
        display.fill(0)
        display.write_text_small("MAX7219", 0, 1)
        time.sleep(1)
        display.write_scrolling_text_small("Hello World!", 1)
        time.sleep(1)
        display.write_scrolling_text_small("ESP32 & MicroPython", 1)
        time.sleep(1)

        ## 3b) Testsequenz für Sonderzeichen der kleinen Schrift
        display.write_scrolling_text_small(":,.°%-_#+*/|=", 1)
        time.sleep(2)

        ## 4) Demo mit kompakter 5x7-Schrift (größere Ziffern für Uhranzeige)
        display.fill(0)
        display.write_text_centered("12:45%°", 1, FONT_5X7)
        time.sleep(2)
        display.fill(0)
        display.write_text_centered("22.1°  50%", 1, FONT_3X5)
        time.sleep(2)

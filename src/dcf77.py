import asyncio
import time

import machine


##==============================================================================
class DCF77:
    ##--------------------------------------------------------------------------
    def __init__(self, pin_no, led_pin=2, debounce_ms=30, on_sync=None, verbose=False):
        ## DCF-Eingang
        self.pin = machine.Pin(pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
        ## Interne LED (meist GPIO 2)
        self.led = machine.Pin(led_pin, machine.Pin.OUT)
        ## Debounce-Zeit in ms (typisch 20-50ms)
        self.debounce_ms = debounce_ms

        ## Variablen für die DCF-Logik
        self.bits = []
        self.last_change_time = time.ticks_ms()
        self.last_stable_state = self.pin.value()
        self.pulse_start_time = 0
        self.last_pulse_end = time.ticks_ms()
        self.sync_ready = False
        self.current_time = None  # (Jahr, Monat, Tag, Wochentag, Std, Min)
        self._line_open = False
        self.on_sync = on_sync
        self.verbose = verbose

    ##--------------------------------------------------------------------------
    def flush_output_line(self):
        """Sorgt für einen sauberen Zeilenumbruch bei Inline-Ausgaben."""
        if self._line_open:
            self.print()
            self._line_open = False

    ##--------------------------------------------------------------------------
    def _bcd_to_int(self, bit_list):
        """Konvertiere eine Liste von Bits (LSB first) in eine Ganzzahl"""
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bit_list):
            # if i < len(weights) and bit:
            if bit:
                val += weights[i]
        return val

    ##--------------------------------------------------------------------------
    def _even_parity_ok(self, bits, parity_bit):
        """DCF77 nutzt gerade Parität: Summe inkl. Paritätsbit muss gerade sein."""
        return (sum(bits) + parity_bit) % 2 == 0

    ##--------------------------------------------------------------------------
    def _select_telegram_bits(self):
        """Nimm bevorzugt die letzten 59, sonst letzten 58 Bits aus dem Buffer."""
        if len(self.bits) >= 59:
            return self.bits[-59:]
        if len(self.bits) >= 58:
            return self.bits[-58:]
        return None

    ##--------------------------------------------------------------------------
    def print(self, *args, end="\n"):
        if self.verbose:
            print(*args, end=end)

    ##--------------------------------------------------------------------------
    def _decode_telegram(self, frame_bits):  # noqa: C901
        """Dekodiere ein Telegramm-Frame zu (Y, M, D, WD, HH, MM, SS, 0)."""
        try:
            if frame_bits is None or len(frame_bits) < 58:
                return None

            ## Startbit (Sekunde 20) sollte 1 sein.
            if frame_bits[20] != 1:
                return None

            ## Paritätsprüfungen für Minute und Stunde.
            if not self._even_parity_ok(frame_bits[21:28], frame_bits[28]):
                return None
            if not self._even_parity_ok(frame_bits[29:35], frame_bits[35]):
                return None

            ## Datums-Parität nur prüfen, wenn das volle 59-Bit-Frame vorliegt.
            if len(frame_bits) >= 59:
                if not self._even_parity_ok(frame_bits[36:58], frame_bits[58]):
                    return None

            ## Bits 21-27: Minute
            minute = self._bcd_to_int(frame_bits[21:28])
            ## Bits 29-34: Stunde
            hour = self._bcd_to_int(frame_bits[29:35])
            ## Bits 36-41: Tag
            day = self._bcd_to_int(frame_bits[36:42])
            ## Bits 45-49: Monat
            month = self._bcd_to_int(frame_bits[45:50])
            ## Bits 50-57: Jahr (zweistellig)
            year = 2000 + self._bcd_to_int(frame_bits[50:58])
            ## Bits 42-44: Wochentag
            weekday = self._bcd_to_int(frame_bits[42:45])

            ## Plausibilitätscheck gegen Fehlinterpretationen.
            if not (0 <= minute <= 59):
                return None
            if not (0 <= hour <= 23):
                return None
            if not (1 <= day <= 31):
                return None
            if not (1 <= month <= 12):
                return None
            if not (1 <= weekday <= 7):
                return None

            return (year, month, day, weekday, hour, minute, 0)
        except Exception as e:
            print("Dekodierungsfehler:", e)
            return None

    ##--------------------------------------------------------------------------
    async def run(self):  # noqa: C901
        print(f"DCF77 Background Task gestartet ({self.pin})...")

        while True:
            current_state = self.pin.value()
            ## Bei jeder Änderung (auch instabil) Zeitstempel merken
            ## (Wichtig, damit der Filter "von vorne" anfängt zu zählen)
            now = time.ticks_ms()

            if current_state != self.last_stable_state:
                ## Software-Filter (Debouncing)
                if time.ticks_diff(now, self.last_change_time) > self.debounce_ms:
                    ## Zustand ist nun stabil gewechselt
                    self.last_stable_state = current_state

                    ## FALLENDE FLANKE (LOW): Ein neuer Puls beginnt
                    if self.last_stable_state == 0:
                        self.led.value(1)   # LED AN

                        ## Prüfen, ob die Pause davor die Minutenmarke war
                        if time.ticks_diff(now, self.last_pulse_end) > 1700:
                            self.print("*", end="")
                            self._line_open = True
                            self.flush_output_line()
                            self.print(f"--- Minute vollständig ({len(self.bits)} Bits). ---")
                            frame = self._select_telegram_bits()
                            self.current_time = self._decode_telegram(frame)
                            if self.current_time:
                                self.sync_ready = True
                                if self.on_sync:
                                    try:
                                        self.on_sync(self.current_time)
                                    except Exception as e:
                                        self.print("on_sync Fehler:", e)
                            self.bits = [] # Buffer leeren für neue Minute
                        self.pulse_start_time = now

                    ## STEIGENDE FLANKE (HIGH): Ein Puls endet
                    else:
                        self.led.value(0)    # LED AUS

                        pulse_dur = time.ticks_diff(now, self.pulse_start_time)
                        self.last_pulse_end = now

                        if 70 < pulse_dur < 150:
                            self.bits.append(0)
                            self.print("0", end="")
                            self._line_open = True
                        elif 170 < pulse_dur < 280:
                            self.bits.append(1)
                            self.print("1", end="")
                            self._line_open = True

                        ## Buffer begrenzen, falls Minutenmarke mehrfach nicht erkannt wurde.
                        if len(self.bits) > 180:
                            self.bits = self.bits[-120:]

                        ## Alle 10 Bits ein Leerzeichen für die Lesbarkeit
                        if len(self.bits) % 10 == 0:
                            self.print(" ", end="")
                            self._line_open = True
            else:
                self.last_change_time = now

            ## Kurze Pause, um anderen Tasks Zeit zu geben
            await asyncio.sleep_ms(5)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## Beispiel für die Integration in main.py
    def handle_sync(sync_time):
        print(f"[SYNC SUCCESS] Zeit: {sync_time}")

    async def main():
        dcf = DCF77(pin_no=13, on_sync=handle_sync, verbose=True)

        ## Task im Hintergrund starten
        asyncio.create_task(dcf.run())

        while True:
            if dcf.sync_ready:
                ## Flag bleibt für Programmlogik nutzbar, ohne hier zu drucken.
                dcf.sync_ready = False  # Flag zurücksetzen

            ## Hier andere Dinge tun (Display etc.)
            await asyncio.sleep(10)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Gekillt.")

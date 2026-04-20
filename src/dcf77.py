import asyncio
import time

import machine


##==============================================================================
class DCF77:
    def __init__(self, pin_no, led_pin=2, debounce_ms=30, on_sync=None):
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

    def flush_output_line(self):
        """Sorgt fuer einen sauberen Zeilenumbruch bei Inline-Ausgaben."""
        if self._line_open:
            print()
            self._line_open = False

    def _bcd_to_int(self, bit_list):
        """Konvertiere eine Liste von Bits (LSB first) in eine Ganzzahl"""
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bit_list):
            # if i < len(weights) and bit:
            if bit:
                val += weights[i]
        return val

    def _decode_telegram(self):
        """Dekodiere die gesammelten Bits zu einem Zeitstempel (Y, M, D, WD, HH, MM, SS, 0)"""
        try:
            ## Wir brauchen mindestens 58 Bits für ein komplettes Telegramm
            if len(self.bits) < 58:
                return

            ## Bits 21-27: Minute
            minute = self._bcd_to_int(self.bits[21:28])
            ## Bits 29-34: Stunde
            hour = self._bcd_to_int(self.bits[29:35])
            ## Bits 36-41: Tag
            day = self._bcd_to_int(self.bits[36:42])
            ## Bits 45-49: Monat
            month = self._bcd_to_int(self.bits[45:50])
            ## Bits 50-57: Jahr (zweistellig)
            year = 2000 + self._bcd_to_int(self.bits[50:58])
            ## Bits 42-44: Wochentag
            weekday = self._bcd_to_int(self.bits[42:45])

            return (year, month, day, weekday, hour, minute, 0, 0)
        except Exception as e:
            print("Dekodierungsfehler:", e)
            return

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
                            print("*", end="")
                            self._line_open = True
                            self.flush_output_line()
                            print(f"--- Minute vollständig ({len(self.bits)} Bits). ---")
                            if len(self.bits) >= 58:
                                self.current_time = self._decode_telegram()
                                if self.current_time:
                                    self.sync_ready = True
                                    if self.on_sync:
                                        try:
                                            self.on_sync(self.current_time)
                                        except Exception as e:
                                            print("on_sync Fehler:", e)
                            self.bits = [] # Buffer leeren für neue Minute
                        self.pulse_start_time = now

                    ## STEIGENDE FLANKE (HIGH): Ein Puls endet
                    else:
                        self.led.value(0)    # LED AUS

                        pulse_dur = time.ticks_diff(now, self.pulse_start_time)
                        self.last_pulse_end = now

                        if 70 < pulse_dur < 150:
                            self.bits.append(0)
                            print("0", end="")
                            self._line_open = True
                        elif 170 < pulse_dur < 280:
                            self.bits.append(1)
                            print("1", end="")
                            self._line_open = True

                        ## Alle 10 Bits ein Leerzeichen für die Lesbarkeit
                        if len(self.bits) % 10 == 0:
                            print(" ", end="")
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
        dcf = DCF77(pin_no=13, on_sync=handle_sync)

        ## Task im Hintergrund starten
        asyncio.create_task(dcf.run())

        while True:
            if dcf.sync_ready:
                ## Flag bleibt fuer Programmlogik nutzbar, ohne hier zu drucken.
                dcf.sync_ready = False  # Flag zurücksetzen

            ## Hier andere Dinge tun (Display etc.)
            await asyncio.sleep(10)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Gekillt.")

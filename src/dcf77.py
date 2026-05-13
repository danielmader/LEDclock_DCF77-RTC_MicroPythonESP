import asyncio
import time

import machine


##==============================================================================
class DCF77:
    ##--------------------------------------------------------------------------
    def __init__(
        self,
        dcf_pin: machine.Pin,
        led_pin: machine.Pin | None = machine.Pin(2, machine.Pin.OUT),
        debounce_ms: int = 30,
        on_sync = None,
        verbose: bool = False,
    ) -> None:
        """Initialisiert den DCF77-Empfänger.

        Parameter
        ---------
        * pin_no: GPIO des DCF77-Datenpins
        * led_pin: GPIO der Status-LED
        * debounce_ms: Entprellzeit für Flanken in Millisekunden
        * on_sync: Optionaler Callback bei erfolgreicher Synchronisation
        * verbose: Aktiviert Debug-Ausgaben

        Returns
        -------
        * None
        """
        ## DCF77-Pin
        self.dcf_pin = dcf_pin
        ## Interne LED (meist GPIO 2)
        if led_pin is None:
            self.led = None
        else:
            self.led = led_pin

        ## Debounce-Zeit in ms (typisch 20-50ms)
        self.debounce_ms = debounce_ms

        ## Variablen für die DCF-Logik
        self.bits = []
        self.last_change_time = time.ticks_ms()
        self.last_stable_state = self.dcf_pin.value()
        self.pulse_start_time = 0
        self.last_pulse_end = time.ticks_ms()
        self.sync_ready = False
        self.current_time = None  # (Jahr, Monat, Tag, Wochentag, Std, Min)
        self._line_open = False
        self.on_sync = on_sync
        self.verbose = verbose

    ##--------------------------------------------------------------------------
    def flush_output_line(self) -> None:
        """Sorgt für einen sauberen Zeilenumbruch bei Inline-Ausgaben.

        Returns
        -------
        * None
        """
        if self._line_open:
            self.printv()
            self._line_open = False

    ##--------------------------------------------------------------------------
    def _bcd_to_int(self, bit_list: list) -> int:
        """Konvertiert eine Liste von DCF-Bits in eine Ganzzahl.

        Parameter
        ---------
        * bit_list: Bitfolge im LSB-first-Format

        Returns
        -------
        * int: Dekodierter Zahlenwert
        """
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bit_list):
            # if i < len(weights) and bit:
            if bit:
                val += weights[i]
        return val

    ##--------------------------------------------------------------------------
    def _even_parity_ok(self, bits: list, parity_bit: int) -> bool:
        """Prüft DCF77-Parität (gerade Parität).

        Parameter
        ---------
        * bits: Nutzdatenbits
        * parity_bit: Zugehöriges Paritätsbit

        Returns
        -------
        * bool: True, wenn die Parität korrekt ist
        """
        return (sum(bits) + parity_bit) % 2 == 0

    ##--------------------------------------------------------------------------
    def _is_leap_year(self, year: int) -> bool:
        """Prüft, ob ein Jahr ein Schaltjahr ist.

        Parameter
        ---------
        * year: Kalenderjahr

        Returns
        -------
        * bool: True bei Schaltjahr
        """
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    ##--------------------------------------------------------------------------
    def _days_in_month(self, year: int, month: int) -> int:
        """Gibt die Anzahl Tage eines Monats zurück.

        Parameter
        ---------
        * year: Kalenderjahr
        * month: Monat 1..12

        Returns
        -------
        * int: Anzahl Tage im Monat
        """
        if month == 2:
            return 29 if self._is_leap_year(year) else 28
        if month in (4, 6, 9, 11):
            return 30
        return 31

    ##--------------------------------------------------------------------------
    def _weekday_dcf_from_date(self, year: int, month: int, day: int) -> int:
        """Berechnet den DCF-Wochentag aus einem Datum.

        Parameter
        ---------
        * year: Kalenderjahr
        * month: Monat 1..12
        * day: Tag 1..31

        Returns
        -------
        * int: Wochentag im DCF-Format (1=Mo..7=So)
        """
        # Sakamoto-Algorithmus: 0=So..6=Sa
        month_table = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
        y = year
        if month < 3:
            y -= 1
        weekday_sun0 = (y + y // 4 - y // 100 + y // 400 + month_table[month - 1] + day) % 7
        if weekday_sun0 == 0:
            return 7
        return weekday_sun0

    ##--------------------------------------------------------------------------
    def _select_telegram_bits(self) -> "list | None":
        """Wählt ein Telegrammfenster aus dem Bitpuffer.

        Returns
        -------
        * list: Letzte 59 bzw. 58 Bits oder None
        """
        if len(self.bits) >= 59:
            return self.bits[-59:]
        if len(self.bits) >= 58:
            return self.bits[-58:]
        return None

    ##--------------------------------------------------------------------------
    def printv(self, *args: object, end: str = "\n") -> None:
        """Gibt Debug-Text nur im Verbose-Modus aus.

        Parameter
        ---------
        * args: Beliebige Druckargumente
        * end: Zeilenende

        Returns
        -------
        * None
        """
        if self.verbose:
            print(*args, end=end)

    ##--------------------------------------------------------------------------
    def _decode_telegram(self, frame_bits: "list | None") -> "tuple | None":  # noqa: C901
        """Dekodiert ein DCF77-Frame in ein Datum/Zeit-Tupel.

        Parameter
        ---------
        * frame_bits: Telegramm-Bits (58 oder 59 Bits)

        Returns
        -------
        * tuple: (year, month, day, weekday, hour, minute, second) oder None
        """
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
            if year < 2000:
                return None

            max_day = self._days_in_month(year, month)
            if day > max_day:
                return None

            expected_weekday = self._weekday_dcf_from_date(year, month, day)
            if weekday != expected_weekday:
                return None

            return (year, month, day, weekday, hour, minute, 0)
        except Exception as e:
            print("Dekodierungsfehler:", e)
            return None

    ##--------------------------------------------------------------------------
    async def run(self) -> None:  # noqa: C901
        """Startet die kontinuierliche DCF77-Decoder-Schleife.

        Returns
        -------
        * None
        """
        print(f"DCF77 Background Task gestartet ({self.dcf_pin})...")

        while True:
            current_state = self.dcf_pin.value()
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
                        if self.led:
                            self.led.value(1)   # LED AN

                        ## Prüfen, ob die Pause davor die Minutenmarke war
                        if time.ticks_diff(now, self.last_pulse_end) > 1700:
                            self.printv("*", end="")
                            self._line_open = True
                            self.flush_output_line()
                            self.printv(f"--- Minute vollständig ({len(self.bits)} Bits). ---")
                            frame = self._select_telegram_bits()
                            self.current_time = self._decode_telegram(frame)
                            if self.current_time:
                                self.sync_ready = True
                                if self.on_sync:
                                    try:
                                        self.on_sync(self.current_time)
                                    except Exception as e:
                                        self.printv("on_sync Fehler:", e)
                            self.bits = [] # Buffer leeren für neue Minute
                        self.pulse_start_time = now

                    ## STEIGENDE FLANKE (HIGH): Ein Puls endet
                    else:
                        if self.led:
                            self.led.value(0)    # LED AUS

                        pulse_dur = time.ticks_diff(now, self.pulse_start_time)
                        self.last_pulse_end = now

                        if 70 < pulse_dur < 150:
                            self.bits.append(0)
                            self.printv("0", end="")
                            self._line_open = True
                        elif 170 < pulse_dur < 280:
                            self.bits.append(1)
                            self.printv("1", end="")
                            self._line_open = True

                        ## Buffer begrenzen, falls Minutenmarke mehrfach nicht erkannt wurde.
                        if len(self.bits) > 180:
                            self.bits = self.bits[-120:]

                        ## Alle 10 Bits ein Leerzeichen für die Lesbarkeit
                        if len(self.bits) % 10 == 0:
                            self.printv(" ", end="")
                            self._line_open = True
            else:
                self.last_change_time = now

            ## Kurze Pause, um anderen Tasks Zeit zu geben
            await asyncio.sleep_ms(5)  # type: ignore[attr-defined]


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## Beispiel für die Integration in main.py
    def handle_sync(sync_time: tuple) -> None:
        """Beispiel-Callback für erfolgreiche DCF-Synchronisation.

        Parameter
        ---------
        * sync_time: Synchronisierte Zeit als Tupel

        Returns
        -------
        * None
        """
        print(f"[SYNC SUCCESS] Zeit: {sync_time}")

    async def main() -> None:
        """Startet den DCF77-Testlauf.

        Returns
        -------
        * None
        """
        dcf_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
        dcf = DCF77(dcf_pin=dcf_pin, on_sync=handle_sync, verbose=True)

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

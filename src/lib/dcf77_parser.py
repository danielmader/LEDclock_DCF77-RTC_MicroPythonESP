import asyncio
import time

import machine  # type: ignore


##==============================================================================
class DCF77Parser:
    def __init__(self, pin_no, led_pin=2):
        ## DCF-Eingang
        self.pin = machine.Pin(pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
        ## Interne LED (meist GPIO 2)
        self.led = machine.Pin(led_pin, machine.Pin.OUT)

        ## Variablen für die DCF-Logik
        self.bits = []
        self.last_change_time = time.ticks_ms()
        self.last_stable_state = self.pin.value()
        self.sync_ready = False
        self.current_time = None  # Hier landet das Ergebnis (Y, M, D, WD, H, M)

    def _bcd_to_int(self, bit_list):
        """Konvertiert eine Liste von Bits (LSB first) in eine Ganzzahl"""
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bit_list):
            if bit:
                val += weights[i]
        return val

    def _decode_telegram(self):
        """Wertet die 59 gesammelten Bits aus"""
        try:
            if len(self.bits) < 59:
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
            now = time.ticks_ms()

            if current_state != self.last_stable_state:
                duration = time.ticks_diff(now, self.last_change_time)

                ## FALLENDE FLANKE (LOW): Ein neuer Puls beginnt
                if current_state == 0:
                    self.led.value(1)   # LED AN

                    ## Wenn die Pause vorher > 1500ms war, ist jetzt eine neue Minute!
                    if duration > 1500: # Minutenpause
                        print(f"\n--- Minute vollständig ({len(self.bits)} Bits). ---")
                        if len(self.bits) >= 58:
                            print("Versuche zu dekodieren...")
                            result = self._decode_telegram()
                            if result:
                                self.current_time = result
                                self.sync_ready = True
                                print(f"Dekodierte Zeit: {result}")
                        self.bits = []  # Liste leeren für die neue Minute

                ## STEIGENDE FLANKE (HIGH): Ein Puls endet
                else:
                    self.led.value(0)    # LED AUS

                    ## Die 'duration' ist hier die Länge des gerade beendeten Low-Pulses
                    if 70 < duration < 140:
                        self.bits.append(0)
                        print("0", end="")
                    elif 170 < duration < 260:
                        self.bits.append(1)
                        print("1", end="")

                    ## Alle 10 Bits ein Leerzeichen für die Lesbarkeit
                    if len(self.bits) % 10 == 0:
                        print(" ", end="")

                self.last_stable_state = current_state
                self.last_change_time = now

            ## Kurze Pause, um anderen Tasks Zeit zu geben
            await asyncio.sleep_ms(10)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## Beispiel für die Integration in main.py
    async def main():
        dcf = DCF77Parser(pin_no=13)

        ## Task im Hintergrund starten
        asyncio.create_task(dcf.run())

        while True:
            if dcf.sync_ready:
                print(f"\n[SYNC SUCCESS] Zeit: {dcf.current_time}")
                dcf.sync_ready = False  # Flag zurücksetzen

            ## Hier andere Dinge tun (Display etc.)
            await asyncio.sleep(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Gekillt.")
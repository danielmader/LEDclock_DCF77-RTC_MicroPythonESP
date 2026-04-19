import asyncio
import machine
import time


##==============================================================================
class DCF77Integrator:
    def __init__(self, pin_no, debounce_ms=30):
        self.pin = machine.Pin(pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
        self.debounce_ms = debounce_ms

        ## Zustandsvariablen für den Filter
        self.last_stable_state = self.pin.value()
        self.last_change_time = time.ticks_ms()

        ## Variablen für die DCF-Logik
        self.bits = []
        self.pulse_start_time = 0
        self.last_pulse_end = time.ticks_ms()
        self.sync_ready = False
        self.current_time = None # (Jahr, Monat, Tag, Wochentag, Std, Min)

    def _bcd_to_int(self, bits):
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bits):
            if i < len(weights) and bit:
                val += weights[i]
        return val

    def _decode_telegram(self):
        try:
            ## Wir brauchen mindestens 58 Bits für ein komplettes Telegramm
            if len(self.bits) < 58: return None

            ## Dekodierung nach DCF77-Standard (BCD)
            m = self._bcd_to_int(self.bits[21:28])
            h = self._bcd_to_int(self.bits[29:35])
            d = self._bcd_to_int(self.bits[36:42])
            wd = self._bcd_to_int(self.bits[42:45])
            mo = self._bcd_to_int(self.bits[45:50])
            y = 2000 + self._bcd_to_int(self.bits[50:58])

            return (y, mo, d, wd, h, m, 0, 0)
        except (ValueError, IndexError) as e:
            print("Fehler bei der Dekodierung:", e)
            return

    async def run(self):
        print(f"DCF77 Background Task gestartet ({self.pin})...")

        while True:
            current_raw_state = self.pin.value()
            now = time.ticks_ms()

            ## Software-Filter (Debouncing)
            if current_raw_state != self.last_stable_state:
                if time.ticks_diff(now, self.last_change_time) > self.debounce_ms:
                    ## Zustand ist nun stabil gewechselt
                    old_state = self.last_stable_state
                    self.last_stable_state = current_raw_state
                    duration = time.ticks_diff(now, self.last_change_time)

                    if self.last_stable_state == 0:  # Puls beginnt (LOW)
                        ## Prüfen, ob die Pause davor die Minutenmarke war
                        if time.ticks_diff(now, self.last_pulse_end) > 1700:
                            if len(self.bits) >= 58:
                                self.current_time = self._decode_telegram()
                                if self.current_time:
                                    self.sync_ready = True
                            self.bits = [] # Buffer leeren für neue Minute
                        self.pulse_start_time = now

                    else: # Puls endet (HIGH)
                        pulse_dur = time.ticks_diff(now, self.pulse_start_time)
                        self.last_pulse_end = now

                        if 70 < pulse_dur < 150:
                            self.bits.append(0)
                        elif 170 < pulse_dur < 280:
                            self.bits.append(1)

                ## Bei jeder Änderung (auch instabil) Zeitstempel merken
                ## (Wichtig, damit der Filter "von vorne" anfängt zu zählen)
            else:
                self.last_change_time = now

            ## Kurze Pause, um anderen Tasks Zeit zu geben
            await asyncio.sleep_ms(5)



##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## Beispiel für die Integration in main.py
    async def main():
        dcf = DCF77Integrator(pin_no=13)

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

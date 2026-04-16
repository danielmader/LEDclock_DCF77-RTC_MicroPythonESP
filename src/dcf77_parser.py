import asyncio
import machine
import time


##==============================================================================
class DCF77Parser:
    def __init__(self, pin_no, led_pin=2):
        ## DCF-Eingang
        self.pin = machine.Pin(pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
        ## Interne LED (meist GPIO 2)
        self.led = machine.Pin(led_pin, machine.Pin.OUT)

        self.bits = []
        self.last_tick = time.ticks_ms()
        self.last_state = self.pin.value()
        self.sync_ready = False
        self.current_time = None  # Hier landet das Ergebnis (Y, M, D, WD, H, M)

    def bcd_to_int(self, bit_list):
        """Konvertiert eine Liste von Bits (LSB first) in eine Ganzzahl"""
        weights = [1, 2, 4, 8, 10, 20, 40, 80]
        val = 0
        for i, bit in enumerate(bit_list):
            if bit:
                val += weights[i]

        return val

    def decode(self):
        """Wertet die 59 gesammelten Bits aus"""
        try:
            if len(self.bits) < 59:
                return

            ## Bits 21-27: Minute
            minute = self.bcd_to_int(self.bits[21:28])
            ## Bits 29-34: Stunde
            hour = self.bcd_to_int(self.bits[29:35])
            ## Bits 36-41: Tag
            day = self.bcd_to_int(self.bits[36:42])
            ## Bits 45-49: Monat
            month = self.bcd_to_int(self.bits[45:50])
            ## Bits 50-57: Jahr (zweistellig)
            year = 2000 + self.bcd_to_int(self.bits[50:58])
            ## Bits 42-44: Wochentag
            weekday = self.bcd_to_int(self.bits[42:45])

            return (year, month, day, weekday, hour, minute, 0, 0)
        except Exception as e:
            print("Dekodierungsfehler:", e)
            return

    async def run(self):
        print("DCF77 Parser aktiv. LED blinkt bei Puls. Warte auf Minutenlücke (ca. 2 Sek. Pause)...")
        while True:
            current_state = self.pin.value()

            if current_state != self.last_state:
                now = time.ticks_ms()
                duration = time.ticks_diff(now, self.last_tick)

                ## FALLENDE FLANKE: Ein neuer Puls beginnt
                if current_state == 0:  # Puls beginnt
                    self.led.value(1)   # LED AN
                    ## Wenn die Pause vorher > 1500ms war, ist jetzt eine neue Minute!
                    if duration > 1500: # Minutenpause
                        print(f"\n--- Minute vollständig ({len(self.bits)} Bits). Dekodiere... ---")
                        if len(self.bits) >= 58:
                            result = self.decode()
                            if result:
                                self.current_time = result
                                self.sync_ready = True
                                print(f"Dekodierte Zeit: {result}")
                        self.bits = []  # Liste leeren für die neue Minute

                ## STEIGENDE FLANKE: Ein Puls endet
                elif current_state == 1: # Puls endet
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

                self.last_state = current_state
                self.last_tick = now

            await asyncio.sleep_ms(10)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":
    async def test():
        dcf = DCF77Parser(27)
        await dcf.run()

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("Test gestoppt.")

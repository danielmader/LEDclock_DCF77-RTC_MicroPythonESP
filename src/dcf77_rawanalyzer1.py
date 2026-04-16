import asyncio
import machine
import time


##==============================================================================
class DCFReceiver:
    def __init__(self, pin):
        self.pin = pin
        self.last_tick = time.ticks_ms()
        self.pulse_width = 0
        self.new_pulse = False

        ## Interrupt bei JEDER Flankenänderung
        self.pin.irq(handler=self.irq_handler, trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING)

    def irq_handler(self, pin):
        now = time.ticks_ms()
        diff = time.ticks_diff(now, self.last_tick)
        self.last_tick = now

        ## Ende des High-Pulses (bei Active-High Modul)
        # if pin.value() == 0:
        #     self.pulse_width = diff
        #     self.new_pulse = True

        ## Wenn der Pin auf 1 geht, ist der LOW-Puls gerade zu Ende gegangen (bei Active-High Modul)
        if pin.value() == 1:
            self.pulse_width = diff
            self.new_pulse = True
        else:
            # Ende der Pause (war auf HIGH)
            # Hier könnte man die Minutenlücke (> 1500ms) erkennen!
            if diff > 1500:
                print("\n--- Minutenpause erkannt ---")

## Pin-Setup mit internem Pull-Up (wichtig für Open Collector!)

dcf_pin = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
dcf = DCFReceiver(dcf_pin)


async def monitor_dcf():
    print("Suche DCF77 Signal... Bitte warten (Antenne ausrichten!)")
    while True:
        if dcf.new_pulse:
            w = dcf.pulse_width
            dcf.new_pulse = False

            if 70 < w < 130:
                print("Bit: 0 (Kurzer Puls)")
            elif 170 < w < 250:
                print("Bit: 1 (Langer Puls)")
            else:
                print(f"? Störung/Pause: {w}ms")

        await asyncio.sleep_ms(10)


async def main():
    print("System-Boot... Starte Tasks.")

    ## Alle Tasks gleichzeitig starten
    await asyncio.gather(
        monitor_dcf()
        # update_display(),
        # read_sensors(),
        # sync_time()
    )

## --- Startschuss --------------------------------------------------------------

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nUhr gestoppt. Kehre zum Prompt zurück.")

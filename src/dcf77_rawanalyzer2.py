import machine
import time

## Pin-Setup mit internem Pull-Up (wichtig für Open Collector!)
dcf_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)

print("DCF77 Raw-Analyzer gestartet...")
print("Pulse ca. 100ms/200ms, Pause ca. 800ms/900ms, Minutenlücke > 1500ms")

last_time = time.ticks_ms()
last_state = dcf_pin.value()

while True:
    current_state = dcf_pin.value()

    if current_state != last_state:
        now = time.ticks_ms()
        duration = time.ticks_diff(now, last_time)

        state_str = "HIGH (Pause)" if last_state == 1 else "LOW  (Puls) "

        ## Wir filtern extremes Rauschen (< 40ms) direkt aus für die Anzeige
        if duration > 40:
            print(f"{time.ticks_ms() / 1000:.3f} : {state_str}: {duration} ms")

        last_state = current_state
        last_time = now

import time

import boardconfig

## Pin-Setup mit internem Pull-Up (wichtig für Open Collector!)
dcf_pin = boardconfig.get_dcf_pin()

## Parameter für die Filterung
DEBOUNCE_MS = 30  # Ignoriere Pegelwechsel, die kürzer als 30ms sind

print("DCF77 Integrations-Analyzer gestartet...")

## Referenzzeitpunkt für die Ausgabe relativer Zeitstempel
t0 = time.ticks_ms()
last_stable_state = dcf_pin.value()
last_change_time = time.ticks_ms()
last_pulse_end = time.ticks_ms()  # wird erst nach dem ersten Puls verwendet (in_pulse)
pulse_start_time = time.ticks_ms()
in_pulse = False

while True:
    current_raw_state = dcf_pin.value()
    now = time.ticks_ms()

    ## Wenn sich der Zustand ändert, warten wir, ob er stabil bleibt
    if current_raw_state != last_stable_state:
        if time.ticks_diff(now, last_change_time) > DEBOUNCE_MS:
            ## Zustand ist stabil!
            old_state = last_stable_state
            last_stable_state = current_raw_state
            duration = time.ticks_diff(now, last_change_time)

            ## Logik für Puls-Auswertung (Low-aktiv)
            if last_stable_state == 0: # Übergang zu Puls (Anfang)
                pulse_start_time = now
                ## Die Zeit seit dem letzten Puls-Ende war die Pause
                if in_pulse:
                    pause_dur = time.ticks_diff(now, last_pulse_end)
                    if pause_dur > 40:  # Rauschen ignorieren
                         print(f"{time.ticks_diff(now, t0) / 1000:.3f} - PAUSE: {pause_dur} ms")

            else:  # Übergang zu Pause (Ende des Pulses)
                pulse_dur = time.ticks_diff(now, pulse_start_time)
                last_pulse_end = now
                in_pulse = True
                if pulse_dur > 40:
                    type_str = "Bit 0" if pulse_dur < 150 else "Bit 1"
                    print(f"{time.ticks_diff(now, t0) / 1000:.3f} - PULS : {pulse_dur} ms ({type_str})")

        ## Wenn der Zustand gerade erst gekippt ist, merken wir uns den Zeitpunkt
        ## aber ändern last_stable_state noch nicht.
    else:
        last_change_time = now

    time.sleep_ms(5)  # entlastet die CPU

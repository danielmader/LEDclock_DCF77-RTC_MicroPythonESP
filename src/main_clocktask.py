import asyncio
import machine
import time


## Zugriff auf die interne Hardware-Uhr
rtc = machine.RTC()

## Beispiel: Einmalig die Zeit setzen (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
# rtc.datetime((2024, 5, 23, 3, 12, 0, 0, 0))

async def clock_task():
    while True:
        ## Wir holen uns die Zeit direkt aus der Hardware
        t = rtc.datetime()
        ## t[4]: Stunde, t[5]: Minute, t[6]: Sekunde
        print(f"Zeit: {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")

        ## Berechnen, wie lange wir bis zur nächsten VOLLEN Sekunde warten müssen
        ## Das minimiert das "Wandern" der Anzeige
        current_ms = time.ticks_ms()
        sleep_time = 1000 - (current_ms % 1000)
        await asyncio.sleep_ms(sleep_time)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":
    try:
        asyncio.run(clock_task())
    except KeyboardInterrupt:
        print("Test gestoppt.")

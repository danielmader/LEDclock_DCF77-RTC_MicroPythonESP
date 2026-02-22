import asyncio
import machine
import time

# Hardware Setup
# RTC initialisieren (interne Uhr des ESP32)
rtc = machine.RTC()

async def update_display():
    """Task: Aktualisiert die Anzeige jede Sekunde"""
    while True:
        t = rtc.datetime()
        # t ist ein Tupel: (Jahr, Monat, Tag, Wochentag, Stunde, Minute, Sekunde, Subsekunde)
        print("Uhrzeit: {:02d}:{:02d}:{:02d}".format(t[4], t[5], t[6]))

        # Hier kommt später dein HUB75- oder Segment-Display-Code hin
        await asyncio.sleep(1)

async def read_sensors():
    """Task: Sensorwerte alle 30 Sekunden lesen"""
    while True:
        # Hier später: bme280.read_temperature()
        print("Sensoren werden gelesen...")
        await asyncio.sleep(30)

async def sync_time():
    """Task: Zeit-Synchronisation (NTP oder DCF77)"""
    while True:
        print("Synchronisiere Zeit...")
        # Hier später: NTP-Abgleich oder DCF77-Logik
        # Beispiel: rtc.datetime((2024, 5, 22, 0, 14, 30, 0, 0))

        # Einmal pro Stunde synchronisieren
        await asyncio.sleep(3600)

async def main():
    # Alle Tasks gleichzeitig starten
    await asyncio.gather(
        update_display(),
        read_sensors(),
        sync_time()
    )

# Startschuss
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Uhr gestoppt.")

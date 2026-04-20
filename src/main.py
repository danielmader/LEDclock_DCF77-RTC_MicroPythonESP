import asyncio
import time

import machine  # type: ignore

from dcf77_parser import DCF77Parser  # type: ignore

## --- Hardware Setup -----------------------------------------------------------
## Interne RTC des ESP32
rtc_internal = machine.RTC()

## I2C für RV-8263 und SHT31 (Pins wie besprochen)
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(23))

## Analog-Pin für TEMT6000
light_sensor = machine.ADC(machine.Pin(34))
light_sensor.atten(machine.ADC.ATTN_11DB)


## --- Hilfsfunktionen für die Hardware -----------------------------------------

def get_external_rtc_time():
    """Liest die Zeit aus der RV-8263 (Register 0x04)"""
    ## Hier kommt der i2c.readfrom_mem(0x51, 0x04, ...) Code
    ## Rückgabe als Tupel: (Y, M, D, HH, MM, SS)
    return (2026, 4, 16, 3, 15, 30, 0)


def get_sensors():
    """Liest SHT31 und TEMT6000"""
    ## Dummy-Werte oder deine Logik von oben
    t, h = 22.5, 48.0
    l_raw = light_sensor.read()
    return t, h, l_raw


def get_sht31_data():
    ## Code für SHT31 (0x2c 0x06)
    return 22.5, 45.0 # Temp, Hum


def get_brightness():
    ## Code für TEMT6000 (adc.read())
    return 65.2 # Prozent


## --- Async Tasks --------------------------------------------------------------

async def update_display():
    """Task: Aktualisiert die Anzeige exakt jede Sekunde"""
    print("Display-Task gestartet.")
    while True:
        t = rtc_internal.datetime()
        ## Formatierung: HH:MM:SS
        print("Uhrzeit: {:02d}:{:02d}:{:02d}".format(t[4], t[5], t[6]))

        ## --- DRIFT-KOMPENSATION ---
        ## Wir berechnen, wie viele Millisekunden bis zur nächsten vollen Sekunde fehlen.
        ## Das verhindert, dass die Anzeige langsam "wandert".
        ms_to_next_second = 1000 - (time.ticks_ms() % 1000)
        await asyncio.sleep_ms(ms_to_next_second)


async def read_sensors():
    """Task: Sensorwerte alle 30 Sekunden lesen"""
    while True:
        temp, hum, lux = get_sensors()
        print(f"[{time.ticks_ms()}] Sensoren -> Temp: {temp}°C, Feuchte: {hum}%, Licht-Rohwert: {lux}")

        ## Hier könnte später die Display-Helligkeit angepasst werden
        await asyncio.sleep(30)


async def sync_time():
    """Task: Zeit-Synchronisation (Interne RTC <- Externe RTC)"""
    while True:
        print("Sync: Abgleich interne RTC mit RV-8263...")

        ## Zeit von der präzisen externen RTC holen
        ext_t = get_external_rtc_time()

        ## Interne RTC setzen: (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
        rtc_internal.datetime((ext_t[0], ext_t[1], ext_t[2], ext_t[3], ext_t[4], ext_t[5], ext_t[6], 0))

        print("Sync abgeschlossen.")

        ## Alle 10 Minuten synchronisieren
        await asyncio.sleep(600)

async def task_sync_rtc():
    """Gleicht die interne ESP-Uhr mit der externen RV-8263 ab (alle 10 Min)"""
    while True:
        print("SYNC: Hole Zeit von externer RTC...")
        ext_t = get_external_rtc_time()

        ## Interne ESP-RTC synchronisieren
        ## Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        rtc_internal.datetime((ext_t[0], ext_t[1], ext_t[2], 0, ext_t[3], ext_t[4], ext_t[5], 0))

        await asyncio.sleep(600) # 10 Minuten warten


async def task_update_display():
    """Aktualisiert das Display (Sekundentakt)"""
    while True:
        # Wir lesen hier die INTERNE ESP-RTC (sehr schnell)
        t = rtc_internal.datetime()
        print(f"DISPLAY: {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")

        # Hier käme die Steuerung für dein HUB75 oder Segment-Display
        await asyncio.sleep(1)


async def task_read_sensors():
    """Liest Sensoren (alle 30 Sekunden)"""
    while True:
        t, h = get_sht31_data()
        b = get_brightness()
        print(f"SENSOR: Temp {t}°C, Hum {h}%, Light {b}%")

        ## Hier könnte man die Helligkeit des Displays an 'b' anpassen
        await asyncio.sleep(30)


##**************************************************************************
##**************************************************************************

## --- Main-Loop ---------------------------------------------------------------
async def main():
    print("System-Boot: Initialisiere Komponenten...")

    ## 1. Instanz erstellen
    dcf = DCF77Parser(27)

    ## 2. Tasks definieren
    ## Wir nutzen gather, um alle Funktionen gleichzeitig "anzuwerfen"
    print("Starte Event-Loop...")
    await asyncio.gather(
        dcf.run(),                # DCF-Parser
        # update_display(),       # Display-Aktualisierung
        # read_sensors(),         # Sensoren (SHT31/Licht)
        # sync_time()
        # sync_logic(dcf)         # eine neue Funktion, die auf dcf.sync_ready wartet
        # task_update_display(),
        # task_read_sensors(),
        # task_sync_rtc()
    )

async def sync_logic(dcf_instance):
    """Prüft im Hintergrund, ob der DCF-Parser neue Daten hat"""
    while True:
        if dcf_instance.sync_ready:
            print(f"\n[SYNC] Neue DCF-Zeit empfangen: {dcf_instance.current_time}")
            # Hier: rtc.datetime(dcf_instance.current_time)
            dcf_instance.sync_ready = False
        await asyncio.sleep(5)


## --- Startschuss --------------------------------------------------------------

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nUhr gestoppt. Kehre zum Prompt zurück.")
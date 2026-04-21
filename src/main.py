import asyncio
import time

import machine  # type: ignore

import dcf77
import rv8263
import sht31
import temt6000

## --- Hardware-Setup ----------------------------------------------------------

print("System-Boot: Initialisiere Komponenten...")

## 1) Interne RTC des ESP32
rtc_internal = machine.RTC()

## 2) I2C-Bus-Initialisierung mit expliziten Pin-Definitionen für die ESP32-Standard-Pins SCL=22 SDA=23 und Pull-ups.
## Mit externen 10k-Widerständen kann 'pull=None' gesetzt werden, ansonsten ist der interne Pull-up hilfreich.
## => Zur Sicherheit interne Pull-ups zusätzlich an.
sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
## freq=100000 (100kHz) ist sehr stabil für RTCs
## => Reduziere auf 50kHz, um Störung des DCF77-Empfangs zu minimieren
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=50000)
print("Initialisiere I²C Bus...")
devices = i2c.scan()
print("Gefundene I²C Adressen:", [hex(d) for d in devices])

## 3) I2C-Geräte erkennen und initialisieren
## Externe RTC 'RV-8263'
rtc_external = rv8263.RV8263(i2c)
rtc_external.init_rtc()
## Temperatur- und Luftfeuchtigkeitssensor SHT31
temphum_sensor = sht31.SHT31(i2c)

## 4) Helligkeitssensor TEMT6000
light_sensor = temt6000.TEMT6000(adc_pin=36)

## 5) DCF77-Sensor
dcf = dcf77.DCF77(pin_no=13)

## --- Hilfsfunktionen ---------------------------------------------------------

pass  # TODO

## --- Async-Tasks -------------------------------------------------------------

async def update_display():
    """Task: Aktualisiere das Display im Sekundentakt"""
    while True:
        # Wir lesen hier die INTERNE ESP-RTC (sehr schnell)
        now = rtc_internal.datetime()  # Format: (year, month, day, weekday, hours, minutes, seconds)
        ## DEBUG
        # print(111111111111111111, now)
        print(f"[DISPLAY] {now[0]}-{now[1]:02d}-{now[2]:02d} | {now[4]:02d}:{now[5]:02d}:{now[6]:02d}")

        ## TODO: Steuerung für HUB75- oder MAX7219-Display

        ## DRIFT-KOMPENSATION
        # await asyncio.sleep(1)
        ## Wir berechnen, wie viele Millisekunden bis zur nächsten vollen Sekunde fehlen.
        ## Das verhindert, dass die Anzeige langsam "wandert".
        ms_to_next_second = 1000 - (time.ticks_ms() % 1000)
        await asyncio.sleep_ms(ms_to_next_second)


async def read_sensors():
    """Task: Sensorwerte alle x Sekunden lesen"""
    while True:
        temp, hum = temphum_sensor.get_measurement()
        _, lux_perc = light_sensor.get_measurement()
        print(f"[SENSORS] {temp:.2f} °C | {hum:.2f} %rF | {lux_perc:.1f} %ADC")

        ## TODO: Anpassung der Display-Helligkeit

        await asyncio.sleep(5)


async def sync_time():
    """Task: Zeit-Synchronisation DCF77 > Externe RTC > Interne RTC"""
    while True:
        ## Zeit des DCF-Moduls auslesen und externe RTC synchronisieren
        if dcf.sync_ready:
            print(f"[SYNC] Neue DCF-Zeit empfangen: {dcf.current_time}")
            dcf.sync_ready = False
            now = dcf.current_time  # DCF: (year, month, day, weekday(1..7), hours, minutes, seconds)
            ## DEBUG
            # print(777777777777777777, now)
            year, month, day, dcf_weekday, hour, minute, second = now
            machine_weekday = rv8263.RV8263.dcf_weekday_to_machine(dcf_weekday)
            rtc_external.set_rtc_time(year, month, day, machine_weekday, hour, minute, second)

        ## Zeit von der präzisen externen RTC holen
        now = rtc_external.get_rtc_time()  # Format: (year, month, day, weekday, hours, minutes, seconds)
        ## DEBUG
        # print(888888888888888888, now)

        ## Interne RTC setzen: (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
        now = rtc_external.get_rtc_time_machine()
        ## DEBUG
        # print(999999999999999999, now)
        if now is not None:
            rtc_internal.datetime(now)
        # print("RTCs synchronisiert.")

        ## Alle 10 Minuten synchronisieren
        # await asyncio.sleep(600)
        ## Alle 60 Sekunden synchronisieren
        # await asyncio.sleep(60)
        ## Alle 10 Sekunden synchronisieren
        await asyncio.sleep(10)


##******************************************************************************
##******************************************************************************

async def main():
    print("Starte Event-Loop...")
    ## Wir nutzen gather, um alle Funktionen gleichzeitig "anzuwerfen"
    await asyncio.gather(
        dcf.run(),              # DCF-Background-Task
        read_sensors(),         # Sensoren (SHT31/Licht)
        sync_time(),            # Zeit-Synchronisation DCF77 > externe RTC > interne RTC
        update_display(),       # Display-Aktualisierung
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nUhr gestoppt. Kehre zum Prompt zurück.")

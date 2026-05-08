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

DCF_MIN_YEAR = 2020
MAX_SYNC_JUMP_SECONDS = 12 * 60 * 60

_last_dcf_candidate = None


def _is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _days_in_month(year, month):
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _is_dcf_datetime_plausible(now):
    year, month, day, dcf_weekday, hour, minute, second = now
    if not (DCF_MIN_YEAR <= year <= 2099):
        return False
    if not (1 <= month <= 12):
        return False
    if not (1 <= day <= _days_in_month(year, month)):
        return False
    if not (1 <= dcf_weekday <= 7):
        return False
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return False
    return True


def _to_epoch_seconds(year, month, day, hour, minute, second):
    try:
        return time.mktime((year, month, day, hour, minute, second, 0, 0))
    except TypeError:
        return time.mktime((year, month, day, hour, minute, second, 0, 0, 0))


def _is_sync_jump_acceptable(dcf_now, rtc_now):
    if rtc_now is None:
        return True

    rtc_year = rtc_now[0]
    if rtc_year < DCF_MIN_YEAR:
        # RTC ist noch uninitialisiert oder hat Default-Zeit.
        return True

    try:
        dcf_epoch = _to_epoch_seconds(dcf_now[0], dcf_now[1], dcf_now[2], dcf_now[4], dcf_now[5], dcf_now[6])
        rtc_epoch = _to_epoch_seconds(rtc_now[0], rtc_now[1], rtc_now[2], rtc_now[4], rtc_now[5], rtc_now[6])
    except Exception:
        return False

    delta = abs(dcf_epoch - rtc_epoch)
    return delta <= MAX_SYNC_JUMP_SECONDS


def should_accept_dcf_sync(dcf_now, rtc_now):
    """Akzeptiere DCF-Zeit nur bei Plausibilität + 2x gleicher Kandidat."""
    global _last_dcf_candidate

    if not _is_dcf_datetime_plausible(dcf_now):
        return False, "DCF-Zeit außerhalb Plausibilitätsbereich"

    if not _is_sync_jump_acceptable(dcf_now, rtc_now):
        return False, "DCF-Sprung zur RTC zu groß"

    if _last_dcf_candidate != dcf_now:
        _last_dcf_candidate = dcf_now
        return False, "warte auf zweite identische Minute"

    _last_dcf_candidate = None
    return True, "ok"

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
            dcf_now = dcf.current_time  # DCF: (year, month, day, weekday(1..7), hours, minutes, seconds)
            rtc_now = rtc_external.get_rtc_time()

            accepted, reason = should_accept_dcf_sync(dcf_now, rtc_now)
            if accepted:
                year, month, day, dcf_weekday, hour, minute, second = dcf_now
                machine_weekday = rv8263.RV8263.dcf_weekday_to_machine(dcf_weekday)
                rtc_external.set_rtc_time(year, month, day, machine_weekday, hour, minute, second)
                print("[SYNC] DCF-Zeit auf RTC übernommen")
            else:
                print(f"[SYNC] DCF-Zeit verworfen ({reason}): {dcf_now}")

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

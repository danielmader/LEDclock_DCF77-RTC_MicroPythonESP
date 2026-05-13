import asyncio
import time

import machine

import dcf77
import max7219wrapper
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
adc_pin = machine.Pin(36)
light_sensor = temt6000.TEMT6000(adc_pin)

## 5) DCF77-Sensor
dcf_pin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
dcf = dcf77.DCF77(dcf_pin, led_pin=None)  # Optional: LED an Pin 2 zur Visualisierung der Signalverarbeitung anschließen

## 6) MAX7219-LED-Matrix (2x 4 Module à 8x8 LEDs = 2x 32x8)
baudrate = 500000  # 500 kHz für maximale Stabilität bei langen Kabeln oder vielen Modulen
spi = machine.SPI(1, baudrate=baudrate, polarity=0, phase=0, sck=machine.Pin(5), mosi=machine.Pin(19))
cs = machine.Pin(18, machine.Pin.OUT)
power_pin = machine.Pin(0, machine.Pin.OUT)
# display = max7219wrapper.Max7219Matrix(spi, cs, num_modules=4, power_pin=power_pin)
display = max7219wrapper.Max7219Matrix(spi, cs, num_modules=8, power_pin=power_pin, modules_per_row=4)

## --- Hilfsfunktionen ---------------------------------------------------------

DCF_MIN_YEAR = 2020
MAX_SYNC_JUMP_SECONDS = 12 * 60 * 60
DCF_PROGRESS_TOLERANCE_SECONDS = 20

_last_dcf_candidate = None
_last_dcf_candidate_ticks = None
_latest_temp = None
_latest_hum = None
_latest_lux_perc = None


def _is_leap_year(year: int) -> bool:
    """Prüft, ob ein Jahr ein Schaltjahr ist.

    Parameter
    ---------
    * year: Kalenderjahr

    Returns
    -------
    * bool: True bei Schaltjahr
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    """Gibt die Anzahl Tage eines Monats zurück.

    Parameter
    ---------
    * year: Kalenderjahr
    * month: Monat 1..12

    Returns
    -------
    * int: Anzahl Tage im Monat
    """
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _is_dcf_datetime_plausible(now: tuple) -> bool:
    """Prüft, ob eine DCF-Zeitangabe in plausiblen Grenzen liegt.

    Parameter
    ---------
    * now: DCF-Zeit als Tupel (Y, M, D, weekday, h, m, s)

    Returns
    -------
    * bool: True bei plausiblen Werten
    """
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


def _to_epoch_seconds(year: int, month: int, day: int, hour: int, minute: int, second: int) -> int:
    """Wandelt Datum/Zeit in Unix-Epoch-Sekunden um.

    Parameter
    ---------
    * year: Jahr
    * month: Monat
    * day: Tag
    * hour: Stunde
    * minute: Minute
    * second: Sekunde

    Returns
    -------
    * int: Epoch-Zeit in Sekunden
    """
    try:
        return time.mktime((year, month, day, hour, minute, second, 0, 0))
    except TypeError:
        return time.mktime((year, month, day, hour, minute, second, 0, 0, 0))


def _is_sync_jump_acceptable(dcf_now: tuple, rtc_now: "tuple | None") -> bool:
    """Prüft, ob der DCF-Zeitsprung gegenüber RTC akzeptabel ist.

    Parameter
    ---------
    * dcf_now: Kandidat aus DCF als Tupel
    * rtc_now: Aktuelle RTC-Zeit als Tupel oder None

    Returns
    -------
    * bool: True, wenn Sprung innerhalb des Limits liegt
    """
    if rtc_now is None:
        return True

    rtc_year = rtc_now[0]
    if rtc_year < DCF_MIN_YEAR:
        ## RTC ist noch uninitialisiert oder hat Default-Zeit.
        return True

    try:
        dcf_epoch = _to_epoch_seconds(dcf_now[0], dcf_now[1], dcf_now[2], dcf_now[4], dcf_now[5], dcf_now[6])
        rtc_epoch = _to_epoch_seconds(rtc_now[0], rtc_now[1], rtc_now[2], rtc_now[4], rtc_now[5], rtc_now[6])
    except Exception:
        return False

    delta = abs(dcf_epoch - rtc_epoch)
    return delta <= MAX_SYNC_JUMP_SECONDS


def _is_dcf_progress_consistent(prev_dcf: tuple, prev_ticks: object, curr_dcf: tuple, curr_ticks: object) -> bool:
    """Prüft, ob DCF-Zeitfortschritt zur real verstrichenen Zeit passt.

    Parameter
    ---------
    * prev_dcf: Vorherige DCF-Zeit
    * prev_ticks: Tick-Zeitstempel der vorherigen DCF-Zeit
    * curr_dcf: Aktuelle DCF-Zeit
    * curr_ticks: Tick-Zeitstempel der aktuellen DCF-Zeit

    Returns
    -------
    * bool: True bei konsistentem Fortschritt
    """
    try:
        prev_epoch = _to_epoch_seconds(prev_dcf[0], prev_dcf[1], prev_dcf[2], prev_dcf[4], prev_dcf[5], prev_dcf[6])
        curr_epoch = _to_epoch_seconds(curr_dcf[0], curr_dcf[1], curr_dcf[2], curr_dcf[4], curr_dcf[5], curr_dcf[6])
    except Exception:
        return False

    dcf_delta = curr_epoch - prev_epoch
    elapsed_seconds = time.ticks_diff(curr_ticks, prev_ticks) // 1000  # type: ignore[arg-type]

    if dcf_delta <= 0:
        return False

    return abs(dcf_delta - elapsed_seconds) <= DCF_PROGRESS_TOLERANCE_SECONDS


def should_accept_dcf_sync(dcf_now: tuple, rtc_now: "tuple | None", recv_ticks: object) -> tuple:
    """Entscheidet, ob eine DCF-Zeit für Synchronisation akzeptiert wird.

    Parameter
    ---------
    * dcf_now: Kandidat aus DCF als Tupel
    * rtc_now: Aktuelle RTC-Zeit als Tupel oder None
    * recv_ticks: Tick-Zeitstempel beim Empfang

    Returns
    -------
    * tuple: (accepted, reason)
    """
    global _last_dcf_candidate, _last_dcf_candidate_ticks

    if not _is_dcf_datetime_plausible(dcf_now):
        return False, "DCF-Zeit außerhalb Plausibilitätsbereich"

    if not _is_sync_jump_acceptable(dcf_now, rtc_now):
        return False, "DCF-Sprung zur RTC zu groß"

    if _last_dcf_candidate is None or _last_dcf_candidate_ticks is None:
        _last_dcf_candidate = dcf_now
        _last_dcf_candidate_ticks = recv_ticks
        return False, "warte auf zeitkonsistente Folge"

    if not _is_dcf_progress_consistent(_last_dcf_candidate, _last_dcf_candidate_ticks, dcf_now, recv_ticks):
        _last_dcf_candidate = dcf_now
        _last_dcf_candidate_ticks = recv_ticks
        return False, "DCF-Folge zeitlich inkonsistent"

    _last_dcf_candidate = dcf_now
    _last_dcf_candidate_ticks = recv_ticks
    return True, "ok"

## --- Async-Tasks -------------------------------------------------------------

async def update_display():
    """Aktualisiert die Anzeige im Sekundentakt.

    Returns
    -------
    * None
    """
    while True:
        global _latest_temp, _latest_hum

        ## Wir lesen hier die INTERNE ESP-RTC (sehr schnell)
        now = rtc_internal.datetime()  # Format: (year, month, day, weekday, hours, minutes, seconds)
        print(f"[DISPLAY] {now[0]}-{now[1]:02d}-{now[2]:02d} | {now[4]:02d}:{now[5]:02d}:{now[6]:02d}")

        ## Display löschen
        display.clear()
        ## 1a) Anzeige der Uhrzeit im Format "HH:MM:SS"
        # time_str = f"{now[4]:02d}:{now[5]:02d}:{now[6]:02d}"
        ## 1b) Anzeige der Uhrzeit im Format "HH:MM" mit blinkendem Doppelpunkt
        if now[6] % 2 == 0:
            time_str = f"{now[4]:02d}:{now[5]:02d}"
        else:
            time_str = f"{now[4]:02d} {now[5]:02d}"
        display.write_text_centered(time_str, 1, max7219wrapper.FONT_5X7, row=0)
        ## 2) Sensorwerte auf der zweiten Zeile anzeigen (z.B. Temperatur und Luftfeuchtigkeit)
        if _latest_temp is None or _latest_hum is None:
            display.write_text_centered("----", 1, max7219wrapper.FONT_3X5, row=1)
        else:
            if now[6] % 10 < 5:
                display.write_text_centered(f"{_latest_temp:.1f} °C", 1, max7219wrapper.FONT_3X5, row=1)
            else:
                display.write_text_centered(f"{_latest_hum:.1f} %", 1, max7219wrapper.FONT_3X5, row=1)
        ## Neue Anzeige schalten
        display.show()

        # await asyncio.sleep(1)
        ## DRIFT-KOMPENSATION
        ## Wir berechnen, wie viele Millisekunden bis zur nächsten vollen Sekunde fehlen.
        ## Das verhindert, dass die Anzeige langsam "wandert".
        ms_to_next_second = 1000 - (time.ticks_ms() % 1000)  # type: ignore[operator]
        await asyncio.sleep_ms(ms_to_next_second)  # type: ignore[attr-defined]


async def read_sensors():
    """Liest periodisch Sensorwerte und schreibt sie ins Log.

    Returns
    -------
    * None
    """
    global _latest_temp, _latest_hum, _latest_lux_perc

    while True:
        temp, hum = temphum_sensor.get_measurement()
        _, lux_perc = light_sensor.get_measurement()

        _latest_temp = temp
        _latest_hum = hum
        _latest_lux_perc = lux_perc

        print(f"[SENSORS] {temp:.2f} °C | {hum:.2f} %rF | {lux_perc:.1f} %ADC")

        ## TODO: Anpassung der Display-Helligkeit
        ## TODO: Anzeige von Temperatur/Luftfeuchtigkeit/Helligkeit auf Display (z.B. im Wechsel mit Uhrzeit oder per Knopfdruck)

        await asyncio.sleep(5)


async def sync_time():
    """Synchronisiert Zeit von DCF77 zur externen und internen RTC.

    Returns
    -------
    * None
    """
    while True:
        ## Zeit des DCF-Moduls auslesen und RTCs synchronisieren
        if dcf.sync_ready:
            dcf.sync_ready = False  # Flag zurücksetzen
            dcf_now = dcf.current_time  # DCF: (year, month, day, weekday(1..7), hours, minutes, seconds)
            if dcf_now is None:
                print("[SYNC] DCF-Signal meldete sync_ready ohne Zeitwert")
                await asyncio.sleep(1)
                continue

            print(f"[SYNC] Neue DCF-Zeit empfangen: {dcf_now}")
            rtc_now = rtc_external.get_rtc_time()
            recv_ticks = time.ticks_ms()

            accepted, reason = should_accept_dcf_sync(dcf_now, rtc_now, recv_ticks)
            if accepted:
                ## Externe RTC synchronisieren: DCF-Zeit -> Externe RTC
                year, month, day, dcf_weekday, hour, minute, second = dcf_now
                machine_weekday = rv8263.RV8263.dcf_weekday_to_machine(dcf_weekday)
                rtc_external.set_rtc_time(year, month, day, machine_weekday, hour, minute, second)
                print("[SYNC] DCF-Zeit auf RTC übernommen")
            else:
                print(f"[SYNC] DCF-Zeit verworfen ({reason}): {dcf_now}")

            ## Interne RTC synchronisieren: Externe RTC -> Interne RTC
            # now = rtc_external.get_rtc_time()  # Format: (year, month, day, weekday, hours, minutes, seconds)
            now = rtc_external.get_rtc_time_machine()  # Format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
            if now is not None:
                rtc_internal.datetime(now)
                print("[SYNC] Interne RTC mit externer RTC synchronisiert")

        await asyncio.sleep(1)


##******************************************************************************
##******************************************************************************

async def main() -> None:
    """Startet alle asynchronen Tasks.

    Returns
    -------
    * None
    """
    print("Starte Event-Loop...")
    ## Wir nutzen gather, um alle Funktionen gleichzeitig "anzuwerfen"
    await asyncio.gather(
        dcf.run(),         # DCF-Background-Task
        read_sensors(),    # Sensoren (SHT31/Licht)
        sync_time(),       # Zeit-Synchronisation DCF77 > externe RTC > interne RTC
        update_display(),  # Display-Aktualisierung
    )

try:
    ## RTC-Sync Externe RTC -> Interne RTC zu Beginn, damit die Uhrzeit direkt korrekt ist
    rtc_now = rtc_external.get_rtc_time_machine()
    if rtc_now is not None:
        rtc_internal.datetime(rtc_now)
        print("[BOOT] Interne RTC mit externer RTC synchronisiert")
    asyncio.run(main())
except KeyboardInterrupt:
    ## Uhr gestoppt
    pass

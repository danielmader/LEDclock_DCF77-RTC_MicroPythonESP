from machine import I2C, Pin
import time

## RV-8263-C7 Register:
# Control1 00
# Control2
# Offset
# RAM
# Seconds 04
# Minutes
# Hours
# Date
# Weekday
# Month
# Year
# Seconds Alarm 0B
# Minutes Alarm
# Hours Alarm
# Date Alarm
# Weekday Alarm
# Timer Value
# Timer Mode 11

# I2C Initialisierung für ESP32 (Original)
# Standard Hardware-Pins: SCL=22, SDA=23
i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=100000)

RTC_ADDR = 0x51  # Standardadresse der RV-8263

def bcd_to_dec(bcd):
    """Konvertiert Binary Coded Decimal zu Dezimal."""
    return (bcd // 16) * 10 + (bcd % 16)

def scan_bus():
    print("Scanne I2C Bus...")
    devices = i2c.scan()
    if not devices:
        print("Fehler: Keine I2C-Geräte gefunden! Verkabelung prüfen.")
        return False
    print(f"Gefundene Geräte: {[hex(d) for d in devices]}")
    return RTC_ADDR in devices

def read_rtc_seconds():
    # Register 0x04 ist bei der RV-8263 das Sekunden-Register
    try:
        data = i2c.readfrom_mem(RTC_ADDR, 0x04, 1)
        # Bit 7 ist oft ein Flag (VL - Voltage Low), daher mit 0x7F maskieren
        seconds_bcd = data[0] & 0x7F
        return bcd_to_dec(seconds_bcd)
    except Exception as e:
        print(f"Fehler beim Lesen der RTC: {e}")
        return None

def read_full_time():
    # Lese 7 Bytes ab Register 0x04
    data = i2c.readfrom_mem(RTC_ADDR, 0x04, 7)
    sec = bcd_to_dec(data[0] & 0x7F)
    min = bcd_to_dec(data[1] & 0x7F)
    hour = bcd_to_dec(data[2] & 0x3F) # 24h Modus Maske
    day = bcd_to_dec(data[3] & 0x3F)
    month = bcd_to_dec(data[5] & 0x1F)
    year = bcd_to_dec(data[6]) + 2000
    return (year, month, day, hour, min, sec)

def dec_to_bcd(dec):
    """Konvertiert Dezimal zu Binary Coded Decimal."""
    return (dec // 10) << 4 | (dec % 10)

def set_rtc_time(year, month, date, weekday, hours, minutes, seconds):
    """
    Stellt die Zeit der RV-8263 ein.
    Register: 0x04=Sek, 0x05=Min, 0x06=Std, 0x07=Tag, 0x08=Wochentag, 0x09=Monat, 0x0A=Jahr
    """
    # Datenpaket vorbereiten (BCD konvertiert)
    # Jahr wird oft zweistellig erwartet (z.B. 24 für 2024)
    data = bytes([
        dec_to_bcd(seconds),
        dec_to_bcd(minutes),
        dec_to_bcd(hours),
        dec_to_bcd(date),
        dec_to_bcd(weekday),
        dec_to_bcd(month),
        dec_to_bcd(year % 100)
    ])

    # In einem Rutsch ab Register 0x04 schreiben
    i2c.writeto_mem(RTC_ADDR, 0x04, data)
    print(f"Zeit gesetzt auf: {hours:02d}:{minutes:02d}:{seconds:02d}")


# Hauptprogramm
if scan_bus():
    print("RV-8263 erkannt.")

    # Beispiel: Setze die Uhr auf den 22. Mai 2024, Mittwoch, 14:30:00
    # (Wochentag: 0=So, 1=Mo, ..., 3=Mi, ... 6=Sa - siehe Datenblatt für genaue Definition)
    # print("Setze Uhrzeit...")
    # set_rtc_time(2024, 5, 22, 3, 14, 30, 0)

    for _ in range(10):
        sec = read_rtc_seconds()
        print(f"Aktuelle Sekunde der RTC: {sec}")
        print("Aktuelle Zeit:", read_full_time())
        time.sleep(1)
else:
    print(f"Warnung: RTC (Adresse {hex(RTC_ADDR)}) nicht gefunden.")

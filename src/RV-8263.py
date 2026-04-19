import machine
import time


## Standardadresse der RV-8263
RTC_ADDR = 0x51

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




##==============================================================================
def scan_bus(i2c):
    print("Scanne I2C Bus...")
    devices = i2c.scan()
    if not devices:
        print("Fehler: Keine I2C-Geräte gefunden! Verkabelung prüfen.")
        return False
    print(f"Gefundene Geräte: {[hex(d) for d in devices]}")
    return RTC_ADDR in devices


##==============================================================================
def init_rtc(i2c):
    print("Initialisiere RTC...")
    ## Register 0x00 (Control 1) auf 0 -> startet den Oszillator
    ## Register 0x01 (Control 2) auf 0 -> löscht Alarme/Interrupts
    # i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    # i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00\x00')
    ## Optional: Einmal eine Test-Zeit schreiben (z.B. 12:00:00)
    ## Register 0x04 ist Sekunden, 0x05 Minuten, 0x06 Stunden
    ## Wir schreiben ab 0x01: Sek=10, Min=0, Std=12 (alles in BCD)
    # i2c.writeto_mem(RTC_ADDR, 0x04, b'\x10\x00\x12')


##==============================================================================
def read_rtc_seconds(i2c):
    ## Register 0x04 ist bei der RV-8263 das Sekunden-Register
    try:
        data = i2c.readfrom_mem(RTC_ADDR, 0x04, 1)
        ## Bit 7 ist oft ein Flag (VL - Voltage Low), daher mit 0x7F maskieren
        seconds_bcd = data[0] & 0x7F
        sec = bcd_to_dec(seconds_bcd)
        print(f"Aktuelle Sekunde der RTC: {sec}")
        return sec
    except Exception as e:
        print(f"Fehler beim Lesen der RTC: {e}")
        return


##==============================================================================
def read_full_time(i2c):
    ## Lese 7 Bytes ab Register 0x04
    data = i2c.readfrom_mem(RTC_ADDR, 0x04, 7)
    sec = bcd_to_dec(data[0] & 0x7F)
    min = bcd_to_dec(data[1] & 0x7F)
    hour = bcd_to_dec(data[2] & 0x3F) # 24h Modus Maske
    day = bcd_to_dec(data[3] & 0x3F)
    month = bcd_to_dec(data[5] & 0x1F)
    year = bcd_to_dec(data[6]) + 2000
    full_time = (year, month, day, hour, min, sec)
    print("Aktuelle Zeit:", full_time)
    return full_time


##==============================================================================
def bcd_to_dec(bcd):
    """Konvertiert Binary Coded Decimal zu Dezimal."""
    return (bcd // 16) * 10 + (bcd % 16)


##==============================================================================
def dec_to_bcd(dec):
    """Konvertiert Dezimal zu Binary Coded Decimal."""
    return (dec // 10) << 4 | (dec % 10)


##==============================================================================
def set_rtc_time(i2c, year, month, date, weekday, hours, minutes, seconds):
    """
    Stellt die Zeit der RV-8263 ein.
    Register: 0x04=Sek, 0x05=Min, 0x06=Std, 0x07=Tag, 0x08=Wochentag, 0x09=Monat, 0x0A=Jahr
    """
    print("Setze Uhrzeit...")
    ## Datenpaket vorbereiten (BCD konvertiert)
    ## Jahr wird oft zweistellig erwartet (z.B. 24 für 2024)
    data = bytes([
        dec_to_bcd(seconds),
        dec_to_bcd(minutes),
        dec_to_bcd(hours),
        dec_to_bcd(date),
        dec_to_bcd(weekday),
        dec_to_bcd(month),
        dec_to_bcd(year % 100)
    ])

    ## In einem Rutsch ab Register 0x04 schreiben
    i2c.writeto_mem(RTC_ADDR, 0x04, data)
    print(f"Zeit gesetzt auf: {hours:02d}:{minutes:02d}:{seconds:02d}")


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## I2C Initialisierung für ESP32 mit Standard Hardware-Pins SCL=22 SDA=23
    i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(23), freq=100000)

    if scan_bus(i2c):
        print("RV-8263 erkannt.")

        ## RTC initialisieren (Oszillator starten, Alarme löschen)
        init_rtc(i2c)

        ## Beispiel: Setze die Uhr auf den 19. April 2026, Sonntag, 13:30:00
        ## (Wochentag: 0=So, 1=Mo, ..., 3=Mi, ... 6=Sa - siehe Datenblatt für genaue Definition)
        set_rtc_time(i2c, 2026, 4, 19, 0, 13, 30, 0)

        for _ in range(10):
            sec = read_rtc_seconds(i2c)
            full_time = read_full_time(i2c)
            time.sleep(1)
    else:
        print(f"Warnung: RTC (Adresse {hex(RTC_ADDR)}) nicht gefunden.")

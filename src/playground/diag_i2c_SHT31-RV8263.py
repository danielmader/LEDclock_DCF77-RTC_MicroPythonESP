"""
Vergleichstest: SHT31 (funktioniert) vs. RTC 0x51 (funktioniert nicht?)
Nutzt nur writeto/readfrom (keine _mem-Funktionen) für direkten Zugriff.
"""
import time

import machine

print("I²C Vergleichstest: SHT31 (0x44) vs RTC (0x51)")
print("=" * 60)

sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=50000)

devices = i2c.scan()
print(f"Gefundene Geräte: {[hex(d) for d in devices]}\n")

##==============================================================================
## Test 1: SHT31 (0x44) - ändert den Sensor-Register-Zeiger manuell
##==============================================================================
print("### Test 1: SHT31 (0x44) - Manueller Registerzugriff ###")
try:
    ## Schreibe Befehl "High Repeatability" 0x2C 0x06
    i2c.writeto(0x44, b'\x2c\x06')
    print("✓ writeto(0x44, Befehl) erfolgreich")

    time.sleep(0.05)

    ## Lese 6 Bytes zurück
    data = i2c.readfrom(0x44, 6)
    print(f"✓ readfrom(0x44, 6) erfolgreich: {' '.join(f'{b:02x}' for b in data)}")

    ## Parse Temperatur
    temp_raw = (data[0] << 8) | data[1]
    temp = -45 + (175 * temp_raw / 65535.0)
    print(f"  → Temperatur (parsiert): {temp:.2f}°C\n")
except Exception as e:
    print(f"❌ SHT31 Fehler: {e}\n")

##==============================================================================
## Test 2: RTC (0x51) - Schreibe Register-Zeiger, lese Zeitdaten
##==============================================================================
print("### Test 2: RTC (0x51) - Manueller Registerzugriff ###")
try:
    ## Schreibe Registeradresse 0x04 (Seconds)
    print("  Versuche: writeto(0x51, [0x04])")
    i2c.writeto(0x51, b'\x04')
    print("  ✓ writeto erfolgreich")

    ## Lese 7 Bytes (Sec, Min, Hour, Date, Weekday, Month, Year)
    print("  Versuche: readfrom(0x51, 7)")
    data = i2c.readfrom(0x51, 7)
    print(f"  ✓ readfrom erfolgreich: {' '.join(f'{b:02x}' for b in data)}")

    ## Parse als BCD
    sec = data[0] & 0x7F
    min_ = data[1] & 0x7F
    hour = data[2] & 0x3F
    date = data[3] & 0x3F
    weekday = data[4] & 0x07
    month = data[5] & 0x1F
    year = data[6]

    print(f"  → Rohbytes: sec={sec:02x}, min={min_:02x}, hour={hour:02x}, "
          f"date={date:02x}, weekday={weekday:02x}, month={month:02x}, year={year:02x}")

    ## Prüfe ob es gültige Zeitdaten sind
    if (sec <= 0x59 and min_ <= 0x59 and hour <= 0x23 and
        date <= 0x31 and month <= 0x12):
        print("  ✓ Zeitwerte sehen PLAUSIBEL aus!")
    else:
        print("  ❌ Zeitwerte sind MÜLL (unrealistisch)")
        print("     Ist das überhaupt eine RV-8263? Falsch verdrahtet?\n")

except OSError as e:
    print(f"  ❌ RTC Fehler: {e}")
    print("     0x51 antwortet auf Scan, aber nicht auf Registerzugriff!")
    print("     → Mögliche Ursachen:")
    print("        1. RTC hat keine/zu wenig Stromversorgung")
    print("        2. RTC ist nicht richtig verlötet")
    print("        3. 0x51 ist kein RV-8263 (anderes Gerät / Fakemodul)")
    print("        4. RTC-Kristall ist kaputt oder wird nicht getaktet\n")

##==============================================================================
## Test 3: Direkter Schreibzugriff auf 0x51 (probe)
##==============================================================================
print("### Test 3: Schreibzugriff auf RTC (0x51) ###")
try:
    print("  Versuche: writeto(0x51, [0x00, 0x00]) - setze Register 0x00 = 0x00")
    i2c.writeto(0x51, b'\x00\x00')
    print("  ✓ writeto erfolgreich")
    time.sleep(0.01)

    ## Versuche direkt zu lesen
    print("  Versuche: writeto(0x51, [0x00]) + readfrom(0x51, 1)")
    i2c.writeto(0x51, b'\x00')
    data = i2c.readfrom(0x51, 1)
    print(f"  ✓ readfrom erfolgreich: {data[0]:02x}")

except OSError as e:
    print(f"  ❌ Fehler: {e}\n")

print("=" * 60)
print("Zusammenfassung:")
print("  - Wenn SHT31 ✓ und RTC ❌: RTC-Hardware-Problem (nicht I2C-Bus)")
print("  - Wenn beide ❌: I2C-Bus-Problem (Pull-ups, Verkabelung)")
print("  - Wenn beide ✓: Software-Treiber-Problem")

from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=100000)
RTC_ADDR = 0x51

def bcd_to_dec(bcd):
    return (bcd // 16) * 10 + (bcd % 16)

def full_init_rv8263():
    print("Sende Start-Kommando an RV-8263...")
    # 1. Control 1 (0x00) auf 0 setzen -> Startet den Oszillator
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    # 2. Control 2 (0x01) auf 0 setzen -> Alarme löschen
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')
    # 3. Test-Zeit schreiben: Sekunden auf Register 0x02!
    # Wir schreiben 0 Sekunden in BCD
    i2c.writeto_mem(RTC_ADDR, 0x02, b'\x00')

def read_seconds():
    # Wir lesen jetzt Register 0x02 (Sekunden)
    data = i2c.readfrom_mem(RTC_ADDR, 0x02, 1)
    # Bit 7 ist das VL-Flag (Voltage Low), das wir ausblenden (0x7F)
    return bcd_to_dec(data[0] & 0x7F)

# Ausführung
full_init_rv8263()
print("Monitor startet (Lese Register 0x02)...")

for _ in range(10):
    print(f"Sekunde: {read_seconds()}")
    time.sleep(1)

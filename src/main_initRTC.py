from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=100000)
RTC_ADDR = 0x51

def init_rtc():
    print("Initialisiere RTC (Stoppe Stop-Bit)...")
    # Register 0x00 (Control 1) auf 0 setzen, um Oszillator zu starten
    # Register 0x01 (Control 2) ebenfalls auf 0 (löscht Alarme/Interrupts)
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')

    # Optional: Einmal eine Test-Zeit schreiben (z.B. 12:00:00)
    # Register 0x01 ist Sekunden, 0x02 Minuten, 0x03 Stunden
    # Wir schreiben ab 0x01: Sek=10, Min=0, Std=12 (alles in BCD)
    # 10 Sekunden in BCD ist 0x10
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x10\x00\x12')

def read_rtc_seconds():
    data = i2c.readfrom_mem(RTC_ADDR, 0x01, 1)
    return (data[0] // 16) * 10 + (data[0] % 16)

# Testlauf
init_rtc()
print("Warte 5 Sekunden auf Fortschritt...")
for i in range(5):
    print(f"Sekunde: {read_rtc_seconds()}")
    time.sleep(1)

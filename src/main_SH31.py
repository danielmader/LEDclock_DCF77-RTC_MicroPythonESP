from machine import I2C, Pin
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=100000)
SHT31_ADDR = 0x44

def read_sht31():
    try:
        # Befehl "High Repeatability" senden (0x2C 0x06)
        i2c.writeto(SHT31_ADDR, b'\x2c\x06')

        # Dem Sensor Zeit zum Messen geben (ca. 20ms)
        time.sleep(0.05)

        # 6 Bytes lesen: [Temp MSB, Temp LSB, CRC, Hum MSB, Hum LSB, CRC]
        data = i2c.readfrom(SHT31_ADDR, 6)

        # Temperatur berechnen
        temp_raw = (data[0] << 8) | data[1]
        temperature = -45 + (175 * temp_raw / 65535.0)

        # Luftfeuchtigkeit berechnen
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * hum_raw / 65535.0

        return temperature, humidity
    except Exception as e:
        print("Fehler beim SHT31:", e)
        return None, None

# Testlauf
print("Lese SHT31 Sensor...")
for _ in range(5):
    t, h = read_sht31()
    if t is not None:
        print(f"Temperatur: {t:.2f} °C | Feuchte: {h:.2f} %")
    time.sleep(2)

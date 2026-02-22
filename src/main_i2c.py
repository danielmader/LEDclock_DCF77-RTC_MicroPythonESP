from machine import I2C, Pin

## I²C Bus 0, Standard Hardware-Pins: SCL=22, SDA=23
i2c = I2C(0, scl=Pin(22), sda=Pin(23), freq=100000)

## Scanner ausführen
devices = i2c.scan()
print("Gefundene I2C Adressen:", [hex(d) for d in devices])

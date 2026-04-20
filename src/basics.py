import time

import machine  # type: ignore
import network  # type: ignore

## 1) I2C-Bus Initialisierung für ESP32 mit Standard Hardware-Pin
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(23), freq=100000)
print("Initialisiere I²C Bus...")
devices = i2c.scan()
print("Gefundene I²C Adressen:", [hex(d) for d in devices])

## 1) WLAN Access Point konfigurieren
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP-WROOM-32', password='micropythoniscool')

print("WLAN AP aktiv. Name: ESP-WROOM-32")
print("IP-Adresse:", ap.ifconfig()[0])

## 2) LED zum Blinken bringen (Pin 2 ist Standard bei WROOM-32)
led = machine.Pin(2, machine.Pin.OUT)

print("Starte Blink-Schleife...")
while True:
    led.value(1)  # LED an
    time.sleep(0.5)
    led.value(0)  # LED aus
    time.sleep(0.5)

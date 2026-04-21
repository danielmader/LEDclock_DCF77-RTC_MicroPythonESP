import time

import machine  # type: ignore
import network  # type: ignore

## 1) Interne RTC (Real Time Clock) initialisieren und aktuelle Zeit ausgeben
rtc = machine.RTC()
current_time = rtc.datetime()  # (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
print("Initiale RTC Zeit:", current_time)
rtc.datetime((2026, 4, 21, 2, 12, 0, 0, 0))  # Beispiel: Setze auf 21. April 2026, Dienstag, 12:00:00
current_time = rtc.datetime()  # (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
print("Aktuelle RTC Zeit:", current_time)

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

## 3) WLAN Access Point konfigurieren
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP-WROOM-32', password='micropythoniscool')

print("WLAN AP aktiv. Name: ESP-WROOM-32")
print("IP-Adresse:", ap.ifconfig()[0])

## 4) LED zum Blinken bringen (Pin 2 ist Standard bei WROOM-32)
led = machine.Pin(2, machine.Pin.OUT)

print("Starte Blink-Schleife...")
while True:
    led.value(1)  # LED an
    time.sleep(0.5)
    led.value(0)  # LED aus
    time.sleep(0.5)

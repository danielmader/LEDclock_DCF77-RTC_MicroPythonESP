import time

import machine  # type: ignore
import network  # type: ignore

import boardconfig

## 1) Interne RTC (Real Time Clock) initialisieren und aktuelle Zeit ausgeben
rtc = machine.RTC()
current_time = rtc.datetime()  # (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
print("Initiale RTC Zeit:", current_time)
rtc.datetime((2026, 4, 21, 2, 12, 0, 0, 0))  # Beispiel: Setze auf 21. April 2026, Dienstag, 12:00:00
current_time = rtc.datetime()  # (Jahr, Monat, Tag, Wochentag, Std, Min, Sek, Subsek)
print("Aktuelle RTC Zeit:", current_time)

## 2) I2C-Bus-Initialisierung (Pins & Frequenz aus Board-Konfiguration board_*.json)
i2c = boardconfig.get_i2c()
print("Initialisiere I²C Bus...")
devices = i2c.scan()
print("Gefundene I²C Adressen:", [hex(d) for d in devices])

## 3) WLAN Access Point konfigurieren (Board-Name als SSID)
board_name = boardconfig.load()["board"]
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=board_name, password='micropythoniscool')

print("WLAN AP aktiv. Name:", board_name)
print("IP-Adresse:", ap.ifconfig()[0])

## 4) LED zum Blinken bringen (Pin aus Board-Konfiguration, z.B. GPIO 2 beim WROOM-32)
led = boardconfig.get_status_led_pin()

print("Starte Blink-Schleife...")
while True:
    if led is not None:
        led.value(1)  # LED an
    time.sleep(0.5)
    if led is not None:
        led.value(0)  # LED aus
    time.sleep(0.5)

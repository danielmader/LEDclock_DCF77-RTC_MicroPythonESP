import network
import machine
import time

# ## 1) WLAN Access Point konfigurieren
# ap = network.WLAN(network.AP_IF)
# ap.active(True)
# ap.config(essid='ESP-WROOM-32', password='micropythoniscool')
#
# print("WLAN AP aktiv. Name: ESP-WROOM-32")
# print("IP-Adresse:", ap.ifconfig()[0])
#
# ## 2) LED zum Blinken bringen (Pin 2 ist Standard bei WROOM-32)
# led = machine.Pin(2, machine.Pin.OUT)
#
# print("Starte Blink-Schleife...")
# while True:
#     led.value(1)  # LED an
#     time.sleep(0.5)
#     led.value(0)  # LED aus
#     time.sleep(0.5)


# from upydcf77 import dcf77
## 1)
# dcf = dcf77.dcf77(machine.Pin(16))
# dcf.debug(True)
# dcf.start()
# while True:
#     lastsig = dcf.get_LastSignal()
#     print(lastsig)
#     timestamp = dcf.get_DateTime(with_seconds=False)
#     print(timestamp)
#     infos = dcf.get_Infos()
#     print(infos)
#     time.sleep(1)
## 2)
# dcf = dcf77.dcf77(machine.Pin(16))
#
# # Starting receiving and decoding
# dcf.start()
#
# rtc = machine.RTC()
#
# # Cutstom irq handler
# def handler():
#     print("It's a new day or year.")
#
# dcf.irq([dcf.IRQ_DAY, dcf.IRQ_YEAR], handler)
#
# print("RTC initalized")
# datetime = rtc.datetime()
# print("Actual time: {:02d}:{:02d} {:02d}.{:02d}.{}".format(datetime[4], datetime[5], datetime[2], datetime[1], datetime[0]))
#
# print("Wait for a valid dcf77 signal")
# while not dcf.get_Infos()['Valid']:
#     pass
#
# print("Found Valid signal")
# datetime = dcf.get_DateTime()
# print("DCF77 time: {:02d}:{:02d} {:02d}.{:02d}.{}".format(datetime[4], datetime[5], datetime[2], datetime[1], datetime[0]))
#
# print("Setting RTC")
# rtc.datetime(datetime)



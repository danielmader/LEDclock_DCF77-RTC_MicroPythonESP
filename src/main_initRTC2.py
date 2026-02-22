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


def force_start_rv8263():
    print("Führe Full-Reset und Start aus...")

    # Ersetze den Schreibvorgang in deinem Skript durch diese Zeile:
    # Wir schreiben auf 0x00 bis 0x01 alles auf Null
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00\x00')

    # # 1. Software Reset senden (laut Datenblatt: Register 0x00 auf 0x58)
    # # Manche Revisionen der RV-8263 brauchen dies zum 'Aufwachen'
    # try:
    #     i2c.writeto_mem(RTC_ADDR, 0x00, b'\x58')
    #     time.sleep(0.1)
    # except:
    #     pass
    #
    # # 2. Control 1 (0x00): STOP-Bit (Bit 0) auf 0, alle anderen auch 0
    # i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    #
    # # 3. Control 2 (0x01): Alle Flags löschen
    # i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')
    #
    # # 4. Sekunden-Register (0x02) initialisieren
    # # WICHTIG: Wir schreiben 0x00, um auch das VL-Flag (Bit 7) zu löschen!
    # i2c.writeto_mem(RTC_ADDR, 0x02, b'\x00')

    print("Initialisierung abgeschlossen. Warte auf Oszillator...")
    time.sleep(1)

def monitor():
    force_start_rv8263()
    for i in range(15):
        # Wir lesen Sekunde (0x02) und Minute (0x03) um zu sehen ob sich IRGENDWAS bewegt
        data = i2c.readfrom_mem(RTC_ADDR, 0x02, 2)
        sec_raw = data[0]
        min_raw = data[1]

        # VL-Flag prüfen (Bit 7)
        vl_flag = "!" if (sec_raw & 0x80) else ""

        sec = bcd_to_dec(sec_raw & 0x7F)
        print(f"Sekunde: {sec:02d} {vl_flag} (Raw Hex: {hex(sec_raw)})")
        time.sleep(1)

monitor()

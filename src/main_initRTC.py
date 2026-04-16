import machine
import time


i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(23), freq=100000)
RTC_ADDR = 0x51


def init_rtc():
    print("Initialisiere RTC (Stoppe Stop-Bit)...")
    ## Register 0x00 (Control 1) auf 0 setzen, um Oszillator zu starten
    ## Register 0x01 (Control 2) ebenfalls auf 0 (löscht Alarme/Interrupts)
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')

    ## Optional: Einmal eine Test-Zeit schreiben (z.B. 12:00:00)
    ## Register 0x01 ist Sekunden, 0x02 Minuten, 0x03 Stunden
    ## Wir schreiben ab 0x01: Sek=10, Min=0, Std=12 (alles in BCD)
    ## 10 Sekunden in BCD ist 0x10
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x10\x00\x12')


def read_rtc_seconds():
    data = i2c.readfrom_mem(RTC_ADDR, 0x01, 1)
    return (data[0] // 16) * 10 + (data[0] % 16)


def full_init_rv8263():
    print("Sende Start-Kommando an RV-8263...")
    ## 1. Control 1 (0x00) auf 0 setzen -> Startet den Oszillator
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    ## 2. Control 2 (0x01) auf 0 setzen -> Alarme löschen
    i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')
    ## 3. Test-Zeit schreiben: Sekunden auf Register 0x02!
    ## Wir schreiben 0 Sekunden in BCD
    i2c.writeto_mem(RTC_ADDR, 0x02, b'\x00')


def force_start_rv8263():
    print("Führe Full-Reset und Start aus...")

    ## Ersetze den Schreibvorgang in deinem Skript durch diese Zeile:
    ## Wir schreiben auf 0x00 bis 0x01 alles auf Null
    i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00\x00')

    # ## 1. Software Reset senden (laut Datenblatt: Register 0x00 auf 0x58)
    # ## Manche Revisionen der RV-8263 brauchen dies zum 'Aufwachen'
    # try:
    #     i2c.writeto_mem(RTC_ADDR, 0x00, b'\x58')
    #     time.sleep(0.1)
    # except:
    #     pass
    #
    # ## 2. Control 1 (0x00): STOP-Bit (Bit 0) auf 0, alle anderen auch 0
    # i2c.writeto_mem(RTC_ADDR, 0x00, b'\x00')
    #
    # ## 3. Control 2 (0x01): Alle Flags löschen
    # i2c.writeto_mem(RTC_ADDR, 0x01, b'\x00')
    #
    # ## 4. Sekunden-Register (0x02) initialisieren
    # ## WICHTIG: Wir schreiben 0x00, um auch das VL-Flag (Bit 7) zu löschen!
    # i2c.writeto_mem(RTC_ADDR, 0x02, b'\x00')

    print("Initialisierung abgeschlossen. Warte auf Oszillator...")
    time.sleep(1)


def bcd_to_dec(bcd):
    return (bcd // 16) * 10 + (bcd % 16)

def read_seconds(register=0x02):
    # Wir lesen jetzt das angegebene Register (Standard: 0x02 für Sekunden)
    data = i2c.readfrom_mem(RTC_ADDR, register, 1)
    # Bit 7 ist das VL-Flag (Voltage Low), das wir ausblenden (0x7F)
    return bcd_to_dec(data[0] & 0x7F)



##******************************************************************************
##******************************************************************************
if __name__ == "__main__":
    ## 1)
    init_rtc()
    print("Warte 15 Sekunden auf Fortschritt...")
    for _ in range(15):
        print(f"Sekunde: {read_rtc_seconds()}")
        time.sleep(1)

    ## 2)
    force_start_rv8263()
    for _ in range(15):
        ## Wir lesen Sekunde (0x02) und Minute (0x03) um zu sehen ob sich IRGENDWAS bewegt
        data = i2c.readfrom_mem(RTC_ADDR, 0x02, 2)
        sec_raw = data[0]
        min_raw = data[1]

        # VL-Flag prüfen (Bit 7)
        vl_flag = "!" if (sec_raw & 0x80) else ""

        sec = bcd_to_dec(sec_raw & 0x7F)
        print(f"Sekunde: {sec:02d} {vl_flag} (Raw Hex: {hex(sec_raw)})")
        time.sleep(1)

    ## 3)
    full_init_rv8263()
    print("Monitor startet (Lese Register 0x02)...")
    for _ in range(15):
        print(f"Sekunde: {read_seconds()}")
        time.sleep(1)

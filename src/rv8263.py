import time

import machine


##==============================================================================
def bcd_to_dec(bcd: int) -> int:
    """Konvertiert Binary Coded Decimal zu Dezimal.

    Parameter
    ---------
    * bcd: BCD-codierter Bytewert

    Returns
    -------
    * int: Dezimalwert
    """
    return (bcd // 16) * 10 + (bcd % 16)

# bcd_to_dec(0x25)  # Beispiel: 0x25 (BCD) -> 25 (Dezimal)
# bcd_to_dec(0x59)  # Beispiel: 0x59 (BCD) -> 59 (Dezimal)


##==============================================================================
def dec_to_bcd(dec: int) -> int:
    """Konvertiert Dezimal zu Binary Coded Decimal.

    Parameter
    ---------
    * dec: Dezimalwert

    Returns
    -------
    * int: BCD-codierter Bytewert
    """
    return (dec // 10) << 4 | (dec % 10)

# dec_to_bcd(25)  # Beispiel: 25 (Dezimal) -> 0x25 (BCD)
# dec_to_bcd(59)  # Beispiel: 59 (Dezimal) -> 0x59 (BCD)


##==============================================================================
class RV8263:
    """
    RV-8263 Register:
        00 Control1
        Control2
        Offset
        RAM
        04 Seconds
        Minutes
        Hours
        Date
        Weekday
        Month
        Year
        0B Seconds Alarm
        Minutes Alarm
        Hours Alarm
        Date Alarm
        Weekday Alarm
        Timer Value
        11 Timer Mode

    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    | Address | Function           | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   00h   | Control1           | TEST  |  SR   | STOP  |  SR   |  CIE  | 12_24 |  CAP  |       |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   01h   | Control2           |  AIE  |  AF   |  MI   |  HMI  |  TF   |       FD      |       |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   02h   | Offset             | MODE  |                     OFFSET                            |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   03h   | RAM                |                            RAM data                           |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   04h   | Seconds            |  OS   |  40   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   05h   | Minutes            |   X   |  40   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |         | Hours (24 hour)    |   X   |   X   |  20   |  10   |   8   |   4   |   2   |   1   |
    |   06h   +--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |         | Hours (12 hour)    |   X   |   X   | AMPM  |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   07h   | Date               |   X   |   X   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   08h   | Weekday            |   X   |   X   |   X   |   X   |   X   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   09h   | Month              |   X   |   X   |   X   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   0Ah   | Year               |  80   |  40   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   0Bh   | Seconds Alarm      | AE_S  |  40   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   0Ch   | Minutes Alarm      | AE_M  |  40   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |         | Hours Alarm (24h)  | AE_H  |   X   |  20   |  10   |   8   |   4   |   2   |   1   |
    |   0Dh   +--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |         | Hours Alarm (12h)  | AE_H  |   X   | AMPM  |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   0Eh   | Date Alarm         | AE_D  |   X   |  20   |  10   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   0Fh   | Weekday Alarm      | AE_W  |   X   |   X   |   X   |   X   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   10h   | Timer Value        |  128  |  64   |  32   |  16   |   8   |   4   |   2   |   1   |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    |   11h   | Timer Mode         |   X   |   X   |   X   |      TD       |  TE   |  TIE  | TI_TP |
    +---------+--------------------+-------+-------+-------+-------+-------+-------+-------+-------+
    """

    ## Standard-I2C-Adresse der RV-8263
    RTC_ADDR = 0x51
    I2C_RETRIES = 2

    ##--------------------------------------------------------------------------
    @staticmethod
    def rv_weekday_to_machine(rv_weekday: int) -> int:
        """Wandelt RV-Wochentag in MicroPython-Format um.

        Parameter
        ---------
        * rv_weekday: Wochentag im RV-Format (0=So..6=Sa)

        Returns
        -------
        * int: Wochentag im MicroPython-Format (0=Mo..6=So)
        """
        return (rv_weekday + 6) % 7

    ##--------------------------------------------------------------------------
    @staticmethod
    def machine_weekday_to_rv(machine_weekday: int) -> int:
        """Wandelt MicroPython-Wochentag in RV-Format um.

        Parameter
        ---------
        * machine_weekday: Wochentag im MicroPython-Format (0=Mo..6=So)

        Returns
        -------
        * int: Wochentag im RV-Format (0=So..6=Sa)
        """
        return (machine_weekday + 1) % 7

    ##--------------------------------------------------------------------------
    @staticmethod
    def dcf_weekday_to_rv(dcf_weekday: int) -> int:
        """Wandelt DCF77-Wochentag in RV-Format um.

        Parameter
        ---------
        * dcf_weekday: Wochentag im DCF-Format (1=Mo..7=So)

        Returns
        -------
        * int: Wochentag im RV-Format (0=So..6=Sa)
        """
        return dcf_weekday % 7

    ##--------------------------------------------------------------------------
    @staticmethod
    def dcf_weekday_to_machine(dcf_weekday: int) -> int:
        """Wandelt DCF77-Wochentag in MicroPython-Format um.

        Parameter
        ---------
        * dcf_weekday: Wochentag im DCF-Format (1=Mo..7=So)

        Returns
        -------
        * int: Wochentag im MicroPython-Format (0=Mo..6=So)
        """
        return (dcf_weekday - 1) % 7

    ##--------------------------------------------------------------------------
    def __init__(self, i2c: machine.I2C) -> None:
        """Initialisiert die RV-8263-Instanz.

        Parameter
        ---------
        * i2c: Initialisierter I2C-Bus

        Returns
        -------
        * None
        """
        self.i2c = i2c
        if not self.scan_bus():
            raise Exception(f"RTC 'RV-8263' nicht gefunden auf Adresse {hex(self.RTC_ADDR)}")

    ##--------------------------------------------------------------------------
    def _read_regs(self, reg: int, length: int) -> bytes:
        """Liest RTC-Register robust mit Fallback-Strategie.

        Parameter
        ---------
        * reg: Startregister
        * length: Anzahl zu lesender Bytes

        Returns
        -------
        * bytes: Gelesene Registerdaten
        """
        last_exc = None
        for _ in range(self.I2C_RETRIES):
            try:
                return self.i2c.readfrom_mem(self.RTC_ADDR, reg, length)
            except OSError as exc:
                last_exc = exc
                try:
                    self.i2c.writeto(self.RTC_ADDR, bytes([reg]))
                    return self.i2c.readfrom(self.RTC_ADDR, length)
                except OSError as exc2:
                    last_exc = exc2
                    time.sleep_ms(2)

        if last_exc is not None:
            raise last_exc
        raise OSError("RTC Lesezugriff fehlgeschlagen")

    ##--------------------------------------------------------------------------
    def _write_regs(self, reg: int, data: bytes) -> None:
        """Schreibt RTC-Register robust mit Fallback-Strategie.

        Parameter
        ---------
        * reg: Startregister
        * data: Zu schreibende Nutzdaten

        Returns
        -------
        * None
        """
        last_exc = None
        for _ in range(self.I2C_RETRIES):
            try:
                self.i2c.writeto_mem(self.RTC_ADDR, reg, data)
                return
            except OSError as exc:
                last_exc = exc
                try:
                    self.i2c.writeto(self.RTC_ADDR, bytes([reg]) + data)
                    return
                except OSError as exc2:
                    last_exc = exc2
                    time.sleep_ms(2)

        if last_exc is not None:
            raise last_exc
        raise OSError("RTC Schreibzugriff fehlgeschlagen")

    ##--------------------------------------------------------------------------
    def scan_bus(self) -> bool:
        """Prüft, ob die RTC-Adresse auf dem I2C-Bus erreichbar ist.

        Returns
        -------
        * bool: True, wenn die RTC gefunden wurde
        """
        # print("Scanne I²C Bus...")
        devices = self.i2c.scan()
        if not devices:
            print("Fehler: Keine I²C-Geräte gefunden! Verkabelung prüfen.")
            return False
        # print(f"Gefundene Geräte: {[hex(d) for d in devices]}")
        return self.RTC_ADDR in devices

    ##--------------------------------------------------------------------------
    def init_rtc(self) -> None:
        """Initialisiert die RTC-Grundregister.

        Returns
        -------
        * None
        """
        print("Initialisiere RTC...")
        ## Register 0x00 (Control 1) auf 0 -> startet den Oszillator
        ## Register 0x01 (Control 2) auf 0 -> löscht Alarme/Interrupts
        # self.i2c.writeto_mem(self.RTC_ADDR, 0x00, b'\x00')
        # self.i2c.writeto_mem(self.RTC_ADDR, 0x01, b'\x00')
        # self.i2c.writeto_mem(self.RTC_ADDR, 0x00, b'\x00\x00')
        self._write_regs(0x00, b'\x00\x00')
        ## Optional: Einmal eine Test-Zeit schreiben (z.B. 12:00:00)
        ## Register 0x04 ist Sekunden, 0x05 Minuten, 0x06 Stunden
        ## Wir schreiben ab 0x01: Sek=10, Min=0, Std=12 (alles in BCD)
        # self.i2c.writeto_mem(self.RTC_ADDR, 0x04, b'\x10\x00\x12')

    ##--------------------------------------------------------------------------
    def get_rtc_seconds(self) -> "int | None":
        """Liest nur die Sekunden aus der RTC.

        Returns
        -------
        * int: Sekundenwert 0..59 oder None bei Fehler
        """
        ## Register 0x04 ist bei der RV-8263 das Sekunden-Register
        try:
            # data = self.i2c.readfrom_mem(self.RTC_ADDR, 0x04, 1)
            data = self._read_regs(0x04, 1)
            ## Bit 7 ist oft ein Flag (VL - Voltage Low), daher mit 0x7F maskieren
            seconds_bcd = data[0] & 0x7F  # 0x7F = 0111 1111, um Bit 7 zu ignorieren
            sec = bcd_to_dec(seconds_bcd)

            return sec
        except Exception as e:
            print(f"Fehler beim Lesen der RTC: {e}")
            return

    ##--------------------------------------------------------------------------
    def get_rtc_time(self) -> "tuple | None":
        """Liefert Zeit im MicroPython-Wochentagsformat.

        Returns
        -------
        * tuple: (Y, M, D, weekday(0=Mo..6=So), h, m, s) oder None
        """
        now = self.get_rtc_time_rv()
        if now is None:
            return None

        year, month, date, rv_weekday, hour, minute, second = now
        machine_weekday = self.rv_weekday_to_machine(rv_weekday)
        return (year, month, date, machine_weekday, hour, minute, second)

    ##--------------------------------------------------------------------------
    def get_rtc_time_rv(self) -> "tuple | None":
        """Liefert rohe RV-Zeit mit RV-Wochentagsformat.

        Returns
        -------
        * tuple: (Y, M, D, weekday(0=So..6=Sa), h, m, s) oder None
        """
        ## Lese 7 Bytes ab Register 0x04
        try:
            # data = self.i2c.readfrom_mem(self.RTC_ADDR, 0x04, 7)
            data = self._read_regs(0x04, 7)
            sec = bcd_to_dec(data[0] & 0x7F)  #   0x7F = 0111 1111, um Bit 7 zu ignorieren
            min = bcd_to_dec(data[1] & 0x7F)  #   0x7F = 0111 1111, um Bit 7 zu ignorieren
            hour = bcd_to_dec(data[2] & 0x3F)  #  0x3F = 0011 1111, um Bit 6-7 zu ignorieren (24h Modus Maske)
            date = bcd_to_dec(data[3] & 0x3F)  #  0x3F = 0011 1111, um Bit 6-7 zu ignorieren
            weekday = data[4] & 0x07  #           0x07 = 0000 0111, um Bit 3-7 zu ignorieren (nur die unteren 3 Bits für Wochentag)
            month = bcd_to_dec(data[5] & 0x1F)  # 0x1F = 0001 1111, um Bit 5-7 zu ignorieren
            year = bcd_to_dec(data[6]) + 2000  # Jahr wird als Offset ab 2000 erwartet

            ## Plausibilitaetscheck gegen uninitialisierte/ungueltige BCD-Daten
            if sec > 59 or min > 59 or hour > 23 or date < 1 or date > 31 or month < 1 or month > 12 or weekday > 6:
                raise ValueError(
                    f"Ungueltige RTC-Daten gelesen: year={year}, month={month}, date={date}, weekday={weekday}, hour={hour}, minute={min}, second={sec}"
                )

            return (year, month, date, weekday, hour, min, sec)
        except Exception as e:
            print(f"Fehler beim Lesen der RTC: {e}")
            return

    ##--------------------------------------------------------------------------
    def get_rtc_time_machine(self) -> "tuple | None":
        """Liefert die Zeit im Format von machine.RTC().datetime().

        Returns
        -------
        * tuple: (Y, M, D, weekday, h, m, s, subseconds) oder None
        """
        now = self.get_rtc_time()
        if now is None:
            return None

        year, month, date, machine_weekday, hour, minute, second = now
        return (year, month, date, machine_weekday, hour, minute, second, 0)

    ##--------------------------------------------------------------------------
    def set_rtc_time(
        self,
        year: int,
        month: int,
        date: int,
        weekday: int,
        hours: int,
        minutes: int,
        seconds: int,
    ) -> None:
        """
        Stellt die Zeit der RV-8263 ein.
        Erwartet weekday im MicroPython-Format (0=Mo..6=So).
        Register: 0x04=Sek, 0x05=Min, 0x06=Std, 0x07=Tag, 0x08=Wochentag, 0x09=Monat, 0x0A=Jahr

        Parameter
        ---------
        * year: Jahr vierstellig
        * month: Monat 1..12
        * date: Tag 1..31
        * weekday: Wochentag 0=Mo..6=So
        * hours: Stunde 0..23
        * minutes: Minute 0..59
        * seconds: Sekunde 0..59

        Returns
        -------
        * None
        """
        try:
            rv_weekday = self.machine_weekday_to_rv(weekday)
            ## Datenpaket vorbereiten (BCD konvertiert)
            ## Jahr wird zweistellig erwartet (z.B. 24 für 2024)
            data = bytes([
                dec_to_bcd(seconds),
                dec_to_bcd(minutes),
                dec_to_bcd(hours),
                dec_to_bcd(date),
                rv_weekday,
                dec_to_bcd(month),
                dec_to_bcd(year % 100)
            ])
            ## In einem Rutsch ab Register 0x04 schreiben
            # self.i2c.writeto_mem(self.RTC_ADDR, 0x04, data)
            self._write_regs(0x04, data)
        except Exception as e:
            print(f"Fehler beim Schreiben der RTC: {e}")
            return

    ##--------------------------------------------------------------------------
    def set_rtc_time_rv(
        self,
        year: int,
        month: int,
        date: int,
        rv_weekday: int,
        hours: int,
        minutes: int,
        seconds: int,
    ) -> None:
        """Setzt die RTC mit rohem RV-Wochentag.

        Parameter
        ---------
        * year: Jahr vierstellig
        * month: Monat 1..12
        * date: Tag 1..31
        * rv_weekday: Wochentag 0=So..6=Sa
        * hours: Stunde 0..23
        * minutes: Minute 0..59
        * seconds: Sekunde 0..59

        Returns
        -------
        * None
        """
        machine_weekday = self.rv_weekday_to_machine(rv_weekday)
        self.set_rtc_time(year, month, date, machine_weekday, hours, minutes, seconds)

    ##--------------------------------------------------------------------------
    def set_rtc_time_from_machine(self, machine_datetime: tuple) -> None:
        """Setzt die RTC aus einem machine.RTC().datetime()-Tupel.

        Parameter
        ---------
        * machine_datetime: Tupel im Format (Y, M, D, weekday, h, m, s, subsec)

        Returns
        -------
        * None
        """
        year, month, date, machine_weekday, hour, minute, second, _ = machine_datetime
        self.set_rtc_time(year, month, date, machine_weekday, hour, minute, second)


##******************************************************************************
##******************************************************************************
if __name__ == "__main__":

    ## I2C-Bus-Initialisierung mit expliziten Pin-Definitionen für die ESP32-Standard-Pins SCL=22 SDA=23 und Pull-ups.
    ## Mit externen 10k-Widerständen kann 'pull=None' gesetzt werden, ansonsten ist der interne Pull-up hilfreich.
    ## => Zur Sicherheit interne Pull-ups zusätzlich an.
    sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
    scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
    ## freq=100000 (100kHz) ist sehr stabil für RTCs
    ## => Reduziere auf 50kHz, um Störung des DCF77-Empfangs zu minimieren
    i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=50000)

    ## Externe RTC initialisieren (Oszillator starten, Alarme löschen)
    rtc_ext = RV8263(i2c)
    rtc_ext.init_rtc()
    print("externe RTC-Zeit:", rtc_ext.get_rtc_time())

    ## Interne RTC initialisieren
    rtc_int = machine.RTC()
    print("interne RTC-Zeit:", rtc_int.datetime())

    ## Beispiel: Setze die Uhr auf den 19. April 2026, Sonntag, 13:30:00
    ## Public API nutzt MicroPython weekday: 0=Mo..6=So
    now = (2026, 4, 19, 6, 13, 30, 0)
    print("Startzeit:       ", now)
    rtc_ext.set_rtc_time(2026, 4, 19, 6, 13, 30, 0)
    now_machine = rtc_ext.get_rtc_time_machine()
    if now_machine is not None:
        rtc_int.datetime(now_machine)
    else:
        print("Interne RTC bleibt unveraendert, da externe RTC-Zeit nicht lesbar ist.")

    ## Aktuelle Zeit auslesen und anzeigen
    for _ in range(10):
        sec = rtc_ext.get_rtc_seconds()
        ext_time = rtc_ext.get_rtc_time()
        print("externe RTC-Zeit:", ext_time, sec)
        int_time = rtc_int.datetime()
        print("interne RTC-Zeit:", int_time)
        time.sleep(1)

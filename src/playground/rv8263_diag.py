"""
Diagnostischer Test für die RV8263 RTC.
Dieser Test hilft, I2C-Bus-Probleme und fehlerhafte Geräte zu identifizieren.
"""
import time

import machine  # type: ignore


def hex_dump(data: bytes, label: str = "Data") -> None:
    """Druckt Bytes in hexadezimal aus.

    Parameter
    ---------
    * data: Bytefolge zur Ausgabe
    * label: Präfix vor dem Dump

    Returns
    -------
    * None
    """
    hex_str = " ".join(f"{b:02x}" for b in data)
    print(f"{label}: [{hex_str}]")


def scan_and_diagnose(freq: int = 50000) -> bool:  # noqa: C901
    """Scannt den I2C-Bus und diagnostiziert das Gerät auf 0x51.

    Parameter
    ---------
    * freq: I2C-Frequenz in Hertz

    Returns
    -------
    * bool: True, wenn der Grundzugriff auf 0x51 möglich war
    """
    print(f"\n=== I²C-Diagnose bei {freq} Hz ===")

    sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
    scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
    i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=freq)

    # Scan
    devices = i2c.scan()
    print(f"Gefundene Geräte: {[hex(d) for d in devices]}")

    if 0x51 not in devices:
        print("❌ 0x51 nicht auf dem Bus gefunden!")
        return False

    print("✓ 0x51 antwortet auf Adresslevel")

    # Versuche, Rohbytes von 0x51 zu lesen (Register 0x00-0x0A)
    print("\nVersuche Rohbytes von 0x51 zu lesen (Register 0x00-0x0A):")
    for reg_start in [0x00, 0x04]:
        try:
            data = i2c.readfrom_mem(0x51, reg_start, 7)
            hex_dump(data, f"Reg 0x{reg_start:02x}-0x{reg_start+6:02x}")

            # Check ob es Müll ist (alle 0xFF oder 0x00 oder unrealistische Werte)
            if all(b == 0xFF for b in data):
                print("  ⚠️ Warnung: Alle Bytes sind 0xFF (ROM/offene Leitung?)")
            elif all(b == 0x00 for b in data):
                print("  ⚠️ Warnung: Alle Bytes sind 0x00 (nicht initialisiert?)")
            else:
                # Prüfe ob es aussieht wie BCD-codierte Zeit (Register 0x04+)
                if reg_start == 0x04:
                    sec = data[0] & 0x7F
                    min_ = data[1] & 0x7F
                    hour = data[2] & 0x3F
                    date = data[3] & 0x3F
                    month = data[5] & 0x1F
                    print(f"  Interpretiert als Zeit: {data[6]:02x}:{hour:02x} {date:02x}.{month:02x} Sek={sec:02x} Min={min_:02x}")

                    # Plausibilitätscheck
                    if sec > 0x59 or min_ > 0x59 or hour > 0x23:
                        print("  ❌ UNGÜLTIGE Zeitwerte (wahrscheinlich Müll)")
                    else:
                        print("  ✓ Zeitwerte sehen plausibel aus")
        except OSError as e:
            print(f"  ❌ Fehler beim readfrom_mem: {e}")

            # Fallback: writeto + readfrom
            print("  Versuche Fallback-Methode (writeto + readfrom)...")
            try:
                i2c.writeto(0x51, bytes([reg_start]))
                data = i2c.readfrom(0x51, 7)
                hex_dump(data, f"  Fallback Reg 0x{reg_start:02x}")
            except OSError as e2:
                print(f"  ❌ Fallback auch fehlgeschlagen: {e2}")

    # Teste Schreiben (Control1 auf 0x00)
    print("\nVersuche, Schreib-Test durchzuführen (Reg 0x00 auf 0x00):")
    try:
        i2c.writeto_mem(0x51, 0x00, b'\x00')
        print("  ✓ writeto_mem erfolgreich")
    except OSError as e:
        print(f"  ❌ writeto_mem fehlgeschlagen: {e}")

        # Fallback
        print("  Versuche Fallback-Methode (writeto)...")
        try:
            i2c.writeto(0x51, b'\x00\x00')
            print("  ✓ writeto Fallback erfolgreich")
        except OSError as e2:
            print(f"  ❌ Fallback auch fehlgeschlagen: {e2}")

    time.sleep(0.1)
    return True


##==============================================================================
##==============================================================================

if __name__ == "__main__":
    print("RV-8263 RTC Diagnostischer Test")
    print("=" * 50)

    # Teste mit verschiedenen Frequenzen
    for freq in [50000, 100000, 400000]:
        try:
            scan_and_diagnose(freq)
        except Exception as e:
            print(f"❌ Fehler bei {freq} Hz: {e}")

    print("\n" + "=" * 50)
    print("Diagnose abgeschlossen.")
    print("\nInterpretation:")
    print("- Wenn 0x51 nicht antwortet: Verkabelung/Stromversorgung prüfen")
    print("- Wenn Bytes 0xFF/0x00 sind: RTC nicht initialisiert oder defekt")
    print("- Wenn unrealistische Zeitwerte: Falsches Gerät oder I2C-Konflikt")
    print("- Wenn ETIMEDOUT/ENODEV: I2C-Bus-Timing-Problem oder zu viele Geräte")

"""
Hardware-Diagnose: I2C-Pin-Konfiguration testen
Versucht verschiedene Pin-Setups, um das ENODEV-Problem zu isolieren.
"""
import time

import machine


def test_pin_config(sda_pin_no: int, scl_pin_no: int, freq: int, description: str, use_in_flag: bool = True) -> bool:
    """
    Testet eine spezifische I2C-Pin-Konfiguration.

    Parameter
    ---------
    * sda_pin_no: GPIO-Nummer für SDA
    * scl_pin_no: GPIO-Nummer für SCL
    * freq: I2C-Frequenz in Hertz
    * description: Beschreibender Name des Tests
    * use_in_flag: True für IN+PULL_UP, False für OPEN_DRAIN

    Returns
    -------
    * bool: True bei erfolgreichem Zugriff auf RTC-Register
    """
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"  Pins: SDA=GPIO{sda_pin_no}, SCL=GPIO{scl_pin_no}, Freq={freq}Hz")
    print(f"  Pin-Modus: {'IN mit PULL_UP' if use_in_flag else 'OPEN_DRAIN'}")

    try:
        if use_in_flag:
            ## Bisherige Konfiguration
            sda_pin = machine.Pin(sda_pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
            scl_pin = machine.Pin(scl_pin_no, machine.Pin.IN, machine.Pin.PULL_UP)
        else:
            ## Alternative: OPEN_DRAIN (üblich für I2C)
            sda_pin = machine.Pin(sda_pin_no, machine.Pin.OPEN_DRAIN)
            scl_pin = machine.Pin(scl_pin_no, machine.Pin.OPEN_DRAIN)

        i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=freq)

        ## Scan
        devices = i2c.scan()
        print(f"  ✓ Scan OK: {[hex(d) for d in devices]}")

        if 0x51 not in devices:
            print("  ❌ 0x51 nicht gefunden!")
            return False

        ## Versuche Lesezugriff
        try:
            data = i2c.readfrom_mem(0x51, 0x04, 7)
            print(f"  ✓ readfrom_mem OK: {' '.join(f'{b:02x}' for b in data)}")
            return True
        except OSError as e:
            print(f"  ❌ readfrom_mem fehlgeschlagen: {e}")
            return False

    except Exception as e:
        print(f"  ❌ Fehler beim Setup: {e}")
        return False


##******************************************************************************
##******************************************************************************

if __name__ == "__main__":
    print("I²C-Pin-Konfiguration Diagnose")
    print("=" * 60)

    results = {}

    ## Test 1: Bisherige Konfiguration mit langsameren Frequenzen
    print("\n### Test 1: Aktuelle Konfiguration (SDA=23, SCL=22, IN+PULL_UP) mit langsamen Frequenzen ###")
    for freq in [10000, 25000, 50000]:
        key = f"10k_pullup_{freq}"
        results[key] = test_pin_config(23, 22, freq, f"IN+PULL_UP mit {freq}Hz", use_in_flag=True)

    ## Test 2: OPEN_DRAIN Modus (typisch für I2C)
    print("\n### Test 2: OPEN_DRAIN Modus (SDA=23, SCL=22) ###")
    for freq in [50000, 100000]:
        key = f"open_drain_{freq}"
        results[key] = test_pin_config(23, 22, freq, f"OPEN_DRAIN mit {freq}Hz", use_in_flag=False)

    ## Test 3: Nur SHT31 ansprechen (ohne RTC) zur Validierung
    print("\n### Test 3: Nur SHT31 auf 0x44 testen (Baseline) ###")
    try:
        sda_pin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)
        scl_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)
        i2c = machine.I2C(0, scl=scl_pin, sda=sda_pin, freq=50000)

        devices = i2c.scan()
        print(f"  Alle Geräte: {[hex(d) for d in devices]}")

        if 0x44 in devices:
            try:
                ## SHT31 Standard-Befehl
                i2c.writeto(0x44, b'\x2c\x06')
                time.sleep(0.05)
                data = i2c.readfrom(0x44, 6)
                print(f"  ✓ SHT31 (0x44) antwortet OK: {' '.join(f'{b:02x}' for b in data)}")
            except OSError as e:
                print(f"  ❌ SHT31 Lesefehler: {e}")
    except Exception as e:
        print(f"  ❌ Test fehlgeschlagen: {e}")

    ## Zusammenfassung
    print("\n" + "=" * 60)
    print("Zusammenfassung:")
    for test_name, success in results.items():
        status = "✓ OK" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print("\n⚠️  Interpretation:")
    print("  - Falls alle Tests fehlschlagen: Hardware-Problem (Verkabelung/Pull-ups)")
    print("  - Falls nur IN+PULL_UP fehlschlägt, OPEN_DRAIN OK: I2C-Modus-Problem")
    print("  - Falls SHT31 OK, aber RTC fehlschlägt: Nur RTC-Gerät defekt")
    print("  - Falls alles fehlschlägt: I2C-Bus komplett blockiert")

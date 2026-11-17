
import pyvisa


# ==========================================
# PCR500M CONFIGURATION
# ==========================================

RESOURCE = "ASRL4::INSTR"

TIMEOUT = 10000
BAUD_RATE = 19200
DATA_BITS = 8


def main():

    rm = None
    instrument = None

    try:
        print("=" * 50)
        print("KIKUSUI PCR500M CONNECTION TEST")
        print("=" * 50)

        rm = pyvisa.ResourceManager()

        print(f"\nConnecting to: {RESOURCE}")

        instrument = rm.open_resource(RESOURCE)

        # Serial communication settings
        instrument.baud_rate = BAUD_RATE
        instrument.data_bits = DATA_BITS
        instrument.parity = pyvisa.constants.Parity.none
        instrument.stop_bits = pyvisa.constants.StopBits.one
        instrument.flow_control = (
            pyvisa.constants.VI_ASRL_FLOW_XON_XOFF
        )

        instrument.timeout = TIMEOUT
        instrument.write_termination = "\n"
        instrument.read_termination = "\n"

        print("[OK] Serial port opened.")

        # Identify instrument
        print("\nQuerying instrument identity...")

        identity = instrument.query("*IDN?").strip()

        print(f"Instrument ID: {identity}")

        if "PCR500M" not in identity.upper():

            print("\n[WARNING] Connected instrument is not identified as PCR500M.")
            return

        print("[OK] PCR500M identified successfully.")

        # Measure AC voltage
        print("\nQuerying AC voltage...")

        response = instrument.query(
            "MEASure:VOLTage:AC?"
        ).strip()

        voltage = float(response)

        print(f"\nMeasured AC Voltage: {voltage:.3f} V")
        print("[OK] Voltage measurement successful.")

    except Exception as error:
        print(f"\n[ERROR] {type(error).__name__}: {error}")

    finally:

        if instrument is not None:
            instrument.close()

        if rm is not None:
            rm.close()

        print("\nPCR500M connection closed.")


if __name__ == "__main__":
    main()

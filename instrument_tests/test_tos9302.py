
import pyvisa


# ==========================================
# INSTRUMENT CONFIGURATION
# ==========================================

RESOURCE = "USB0::0x0B3E::0x104F::ZC001527::INSTR"

TIMEOUT = 5000


def main():

    rm = None
    instrument = None

    try:
        print("=" * 50)
        print("KIKUSUI TOS9302 CONNECTION TEST")
        print("=" * 50)

        # Initialize VISA
        rm = pyvisa.ResourceManager()

        # Check available VISA resources
        print("\n=== AVAILABLE VISA RESOURCES ===")

        resources = rm.list_resources()

        for resource in resources:
            print(resource)

        if RESOURCE not in resources:
            raise RuntimeError(
                f"TOS9302 resource not found: {RESOURCE}"
            )

        # Connect instrument
        print("\n=== CONNECTING TOS9302 ===")
        print(f"Resource: {RESOURCE}")

        instrument = rm.open_resource(RESOURCE)

        instrument.timeout = TIMEOUT
        instrument.write_termination = "\n"
        instrument.read_termination = "\n"

        print("[OK] USB connection opened.")

        # Identify instrument
        print("\n=== IDENTIFICATION ===")

        identity = instrument.query("*IDN?").strip()

        print(f"Instrument ID: {identity}")

        if "TOS9302" not in identity.upper():
            print(
                "[WARNING] Connected instrument identity "
                "does not match TOS9302."
            )
        else:
            print("[OK] TOS9302 successfully identified.")

        print("\n=== CONNECTION TEST COMPLETED ===")

    except Exception as error:
        print(f"\n[ERROR] {type(error).__name__}: {error}")

    finally:

        if instrument is not None:
            instrument.close()
            print("\nInstrument connection closed.")

        if rm is not None:
            rm.close()
            print("VISA Resource Manager closed.")


if __name__ == "__main__":
    main()

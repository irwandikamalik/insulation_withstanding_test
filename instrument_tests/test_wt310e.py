import pyvisa
import time
from datetime import datetime


# ==========================================
# INSTRUMENT CONFIGURATION
# ==========================================

RESOURCE = (
    "USB0::0x0B21::0x0025::43335348303130303145::INSTR"
)

TIMEOUT = 5000

MEASUREMENT_DURATION = 10  # seconds
SAMPLE_INTERVAL = 1        # seconds


# ==========================================
# MEASUREMENT FUNCTION
# ==========================================

def measure_voltage_current(instrument):

    measurements = []

    start_time = time.monotonic()
    next_sample_time = start_time

    print("\nStarting measurement...")
    print(f"Duration : {MEASUREMENT_DURATION} seconds")
    print(f"Interval : {SAMPLE_INTERVAL} second(s)")

    print("-" * 65)
    print(
        f"{'No.':<5}"
        f"{'Time':<15}"
        f"{'Voltage (V)':<20}"
        f"{'Current (A)':<20}"
    )
    print("-" * 65)

    sample_number = 0

    while True:

        current_time = time.monotonic()
        elapsed_time = current_time - start_time

        if elapsed_time >= MEASUREMENT_DURATION:
            break

        sample_number += 1

        # Read voltage
        voltage = float(
            instrument.query(
                ":NUMERIC:NORMAL:VALUE? 1"
            ).strip()
        )

        # Read current
        current = float(
            instrument.query(
                ":NUMERIC:NORMAL:VALUE? 2"
            ).strip()
        )

        timestamp = datetime.now().strftime("%H:%M:%S")

        measurements.append({
            "time": timestamp,
            "elapsed": elapsed_time,
            "voltage": voltage,
            "current": current,
        })

        print(
            f"{sample_number:<5}"
            f"{timestamp:<15}"
            f"{voltage:<20.3f}"
            f"{current:<20.4f}"
        )

        next_sample_time += SAMPLE_INTERVAL

        remaining = next_sample_time - time.monotonic()

        if remaining > 0:
            time.sleep(remaining)

    print("-" * 65)

    return measurements


# ==========================================
# STATISTICS
# ==========================================

def show_statistics(measurements):

    if not measurements:
        print("No measurement data available.")
        return

    voltages = [
        item["voltage"] for item in measurements
    ]

    currents = [
        item["current"] for item in measurements
    ]

    print("\nMEASUREMENT SUMMARY")
    print("=" * 50)

    print(f"Total Samples : {len(measurements)}")

    print("\nVoltage:")
    print(f"Average : {sum(voltages) / len(voltages):.3f} V")
    print(f"Minimum : {min(voltages):.3f} V")
    print(f"Maximum : {max(voltages):.3f} V")

    print("\nCurrent:")
    print(f"Average : {sum(currents) / len(currents):.4f} A")
    print(f"Minimum : {min(currents):.4f} A")
    print(f"Maximum : {max(currents):.4f} A")


# ==========================================
# MAIN
# ==========================================

def main():

    rm = None
    instrument = None

    try:

        print("=" * 50)
        print("WT310E VOLTAGE & CURRENT TEST")
        print("=" * 50)

        rm = pyvisa.ResourceManager()

        print(f"Connecting to: {RESOURCE}")

        instrument = rm.open_resource(RESOURCE)

        instrument.timeout = TIMEOUT
        instrument.write_termination = "\n"
        instrument.read_termination = "\n"

        # Identify instrument
        identity = instrument.query("*IDN?").strip()

        print(f"\nInstrument ID: {identity}")
        print("[OK] WT310E connected.")

        # Configure numeric output
        instrument.write(":NUMERIC:FORMAT ASCII")

        # Item 1 = Voltage
        instrument.write(
            ":NUMERIC:NORMAL:ITEM1 U,1"
        )

        # Item 2 = Current
        instrument.write(
            ":NUMERIC:NORMAL:ITEM2 I,1"
        )

        time.sleep(0.5)

        # Measurement
        measurements = measure_voltage_current(
            instrument
        )

        # Summary
        show_statistics(measurements)

    except Exception as error:

        print(f"\n[ERROR] {type(error).__name__}: {error}")

    finally:

        if instrument is not None:
            instrument.close()

        if rm is not None:
            rm.close()

        print("\nWT310E connection closed.")


if __name__ == "__main__":
    main()
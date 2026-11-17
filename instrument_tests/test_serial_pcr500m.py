
import serial
import serial.tools.list_ports
import time


# ==================================================
# PCR500M SERIAL CONFIGURATION
# ==================================================

SERIAL_CONFIG = {
    "port": "COM4",
    "baudrate": 9600,
    "bytesize": serial.EIGHTBITS,
    "parity": serial.PARITY_NONE,
    "stopbits": serial.STOPBITS_ONE,
    "timeout": 3,
    "write_timeout": 3,

    # PCR500M F.CTL = ON
    "xonxoff": True,

    "rtscts": False,
    "dsrdtr": False,
}


class PCR500MSerial:

    def __init__(self, config):
        self.config = config
        self.instrument = None

    def scan_ports(self):
        print("\n=== AVAILABLE SERIAL PORTS ===")

        for port in serial.tools.list_ports.comports():
            print(f"{port.device} - {port.description}")

    def connect(self):
        if self.instrument and self.instrument.is_open:
            print("[INFO] Already connected")
            return True

        try:
            print("\n=== CONNECTING PCR500M ===")
            print("Port:", self.config["port"])
            print("Baudrate:", self.config["baudrate"])
            print("XON/XOFF:", self.config["xonxoff"])

            self.instrument = serial.Serial(**self.config)

            time.sleep(0.5)

            print("[SUCCESS] Serial connection opened")
            return True

        except serial.SerialException as error:
            self.instrument = None
            print("[ERROR] Serial connection failed")
            print(repr(error))
            return False

    def disconnect(self):
        if self.instrument and self.instrument.is_open:
            self.instrument.close()
            print("[INFO] Serial connection closed")

        self.instrument = None

    def send_command(self, command):
        if not self.instrument or not self.instrument.is_open:
            print("[ERROR] Instrument not connected")
            return None

        try:
            self.instrument.reset_input_buffer()

            message = (command + "\n").encode("ascii")

            print(f"\nTX: {message!r}")

            self.instrument.write(message)
            self.instrument.flush()

            response = self.instrument.readline()

            print(f"RX: {response!r}")

            return response.decode(
                "ascii",
                errors="replace"
            ).strip()

        except (serial.SerialException, OSError) as error:
            print("[ERROR] Communication failed:", repr(error))
            return None


# ==================================================
# MAIN
# ==================================================

def main():

    pcr = PCR500MSerial(SERIAL_CONFIG)

    pcr.scan_ports()

    try:
        if not pcr.connect():
            return

        print("\n=== PCR500M CONNECTION TEST ===")

        # IMPORTANT:
        # *IDN? is a provisional test command.
        # Confirm command support in the PCR-M communication manual.
        response = pcr.send_command("*IDN?")

        if response:
            print("[SUCCESS] Response received")
        else:
            print("[WARNING] No response received")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")

    finally:
        pcr.disconnect()


if __name__ == "__main__":
    main()

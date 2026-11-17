
from serial.tools import list_ports

print("=" * 50)
print("WINDOWS SERIAL PORT DETECTION")
print("=" * 50)

ports = list_ports.comports()

for port in ports:
    print(f"\nPort       : {port.device}")
    print(f"Description: {port.description}")
    print(f"Hardware ID: {port.hwid}")
    print(f"Manufacturer: {port.manufacturer}")
    print(f"VID        : {port.vid}")
    print(f"PID        : {port.pid}")

if not ports:
    print("\nNo serial ports detected.")

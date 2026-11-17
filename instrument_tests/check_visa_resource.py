
import pyvisa

def check_visa_resources():
    rm = pyvisa.ResourceManager()

    print("=" * 60)
    print("       VISA RESOURCE SCANNER")
    print("=" * 60)

    print(f"\nVISA Backend: {rm.visalib}")

    resources = rm.list_resources()

    if not resources:
        print("\nTidak ada VISA resource yang terdeteksi.")
    else:
        print(f"\nDitemukan {len(resources)} resource:\n")

        for index, resource in enumerate(resources, start=1):
            print(f"{index}. {resource}")

    print("\n" + "=" * 60)

    # Deteksi COM Port melalui VISA
    print("\nMencari COM Port:")

    for port in range(1, 21):
        resource = f"ASRL{port}::INSTR"

        try:
            instrument = rm.open_resource(resource)
            print(f"[TERSEDIA] {resource}")
            instrument.close()
        except Exception:
            pass

    rm.close()


if __name__ == "__main__":
    check_visa_resources()

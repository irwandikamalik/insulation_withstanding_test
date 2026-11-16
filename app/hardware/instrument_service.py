from app.hardware.exceptions import HardwareIntegrationError


class InstrumentService:
    """
    Safe integration boundary for real instruments.

    Implement and verify the methods below against the exact instrument
    manuals, installed options, wiring and safety procedure before enabling
    HARDWARE_INTEGRATION_READY.

    Never replace these methods with guessed SCPI commands.
    """

    def run_insulation_test(self, model, product_configuration):
        raise HardwareIntegrationError(
            "TOS9200 insulation driver is not implemented and verified."
        )

    def run_withstanding_test(self, model, product_configuration):
        raise HardwareIntegrationError(
            "TOS9200 withstand driver is not implemented and verified."
        )

    def verify_pcr_voltage(self, model, product_configuration):
        raise HardwareIntegrationError(
            "PCR2000 voltage readback driver and model limits "
            "are not configured."
        )

    def safe_shutdown(self):
        # Must be implemented and verified using the instrument manuals.
        # A communication exception does NOT prove that HV output is off.
        pass

from app.database import InstrumentDatabase
from app.hardware.exceptions import HardwareIntegrationError


class InstrumentService:
    """
    Safe integration boundary for real instruments.

    Implement and verify the methods below against the exact instrument
    manuals, installed options, wiring and safety procedure before enabling
    HARDWARE_INTEGRATION_READY.

    Never replace these methods with guessed SCPI commands.
    """

    def __init__(self, instrument_database):
        self.instrument_database = instrument_database

    def validate_configuration(self, product_configuration=None):
        rows = self.instrument_database.get_all_instruments()

        enabled = [row for row in rows if row[5]]
        configured_models = {row[1] for row in enabled}

        required = {"WT310E", "PCR2000", "TOS9200"}
        missing = required - configured_models

        if missing:
            raise HardwareIntegrationError(
                "Enabled instrument configuration missing: "
                + ", ".join(sorted(missing))
            )

        for row in enabled:
            _, model, interface, resource, timeout, _ = row

            if not interface or not resource:
                raise HardwareIntegrationError(
                    f"{model} has incomplete communication configuration."
                )

        if product_configuration is not None:
            product_name = product_configuration.get(
                "model_name", "Unknown"
            )

            per_instrument = product_configuration.get(
                "instruments", {}
            )

            for instrument_model, definitions in (
                InstrumentDatabase.INSTRUMENT_MODELS.items()
            ):
                values = per_instrument.get(instrument_model, {})

                missing_settings = [
                    key
                    for key, _label in definitions
                    if not str(values.get(key, "")).strip()
                ]

                if missing_settings:
                    raise HardwareIntegrationError(
                        f"Product '{product_name}' has incomplete "
                        f"{instrument_model} settings: "
                        f"{', '.join(missing_settings)}"
                    )

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

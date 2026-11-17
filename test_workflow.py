from app.workflows.test_sequence import build_test_sequence
from app.workflows.test_sequence_engine import TestSequenceEngine


class MockInstrumentConfigurationService:

    def validate_configuration(self, product_configuration):
        print("Instrument configuration validated.")


class MockInstrumentService:

    def run_insulation_test(self, model, configuration):
        print("Insulation test executed.")

        return {
            "value": 100,
            "normal": 100,
            "minimum": 50,
            "passed": True,
        }

    def run_withstanding_test(self, model, configuration):
        print("Withstanding test executed.")

        return {
            "value": 1500,
            "normal": 1500,
            "maximum": 2000,
            "passed": True,
        }

    def verify_pcr_voltage(self, model, configuration):
        print("PCR voltage verification executed.")

        return {
            "value": 220,
            "passed": True,
        }

    def safe_shutdown(self):
        print("Mock safe shutdown executed.")


def show_progress(message):
    print(message)


if __name__ == "__main__":

    configuration_service = (
        MockInstrumentConfigurationService()
    )

    instrument_service = MockInstrumentService()

    sequence = build_test_sequence(
        configuration_service,
        instrument_service
    )

    engine = TestSequenceEngine(sequence)

    context = {
        "operator_id": "OP001",
        "model": "MODEL-A",
        "history_tag": "HIST001",
        "door_top": "TOP001",
        "door_bottom": "BOTTOM001",

        "product_configuration": {
            "model_name": "MODEL-A",
            "instruments": {
                "WT310E": {},
                "PCR2000": {},
                "TOS9200": {},
            },
        },

        "judgment": None,
    }

    try:

        engine.execute(
            context,
            progress_callback=show_progress
        )

        print("\nTest Result:", context["judgment"])
        print("Test Completed:", context["test_completed"])

    except Exception as error:

        print("\nWorkflow Error:", error)
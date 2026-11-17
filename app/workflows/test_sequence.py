from app.workflows.test_steps.validate_input import (
    ValidateInputStep,
)

from app.workflows.test_steps.validate_product import (
    ValidateProductStep,
)

from app.workflows.test_steps.validate_instrument import (
    ValidateInstrumentStep,
)

from app.workflows.test_steps.insulation_test import (
    InsulationTestStep,
)

from app.workflows.test_steps.withstanding_test import (
    WithstandingTestStep,
)

from app.workflows.test_steps.verify_pcr_voltage import (
    VerifyPCRVoltageStep,
)

from app.workflows.test_steps.finalize_result import (
    FinalizeResultStep,
)


def build_test_sequence(
    instrument_configuration_service,
    instrument_service
):

    return [

        # Input and configuration validation
        ValidateInputStep(),
        ValidateProductStep(),
        ValidateInstrumentStep(
            instrument_configuration_service
        ),

        # Instrument testing
        InsulationTestStep(instrument_service),
        WithstandingTestStep(instrument_service),
        VerifyPCRVoltageStep(instrument_service),

        # Finalization
        FinalizeResultStep(),

    ]
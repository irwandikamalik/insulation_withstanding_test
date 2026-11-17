from app.workflows.test_steps.base_step import BaseTestStep


class ValidateInstrumentStep(BaseTestStep):

    step_id = "validate_instrument"
    name = "Validate Instrument Configuration"

    def __init__(self, configuration_service):
        super().__init__()
        self.configuration_service = configuration_service

    def execute(self, context):

        self.configuration_service.validate_configuration(
            context["product_configuration"]
        )
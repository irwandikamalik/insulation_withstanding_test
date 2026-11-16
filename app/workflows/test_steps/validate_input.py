from app.workflows.test_steps.base_step import BaseTestStep


class ValidateInputStep(BaseTestStep):

    step_id = "validate_input"
    name = "Validate Input"

    def execute(self, context):
        print("Validating input...")

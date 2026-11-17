from app.workflows.test_steps.base_step import BaseTestStep


class ValidateInputStep(BaseTestStep):

    step_id = "validate_input"
    name = "Validate Input"

    REQUIRED_FIELDS = [
        "operator_id",
        "model",
        "history_tag",
        "door_top",
        "door_bottom",
    ]

    def execute(self, context):

        for field in self.REQUIRED_FIELDS:

            value = context.get(field)

            if value is None or not str(value).strip():
                raise ValueError(
                    f"Required input '{field}' is missing."
                )
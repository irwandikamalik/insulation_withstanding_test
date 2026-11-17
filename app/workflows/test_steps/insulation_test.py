from app.workflows.test_steps.base_step import BaseTestStep
from app.core.exceptions import TestStopped


class InsulationTestStep(BaseTestStep):

    step_id = "insulation_test"
    name = "Insulation Test"

    def __init__(self, instrument_service):
        super().__init__()
        self.instrument_service = instrument_service

    def execute(self, context):

        context["hardware_test_started"] = True

        measurement = self.instrument_service.run_insulation_test(
            context["model"],
            context["product_configuration"]
        )

        context["insulation_test"] = measurement["value"]
        context["insulation_normal"] = measurement.get("normal")
        context["insulation_min"] = measurement.get("minimum")

        if not measurement["passed"]:
            context["judgment"] = "NG"

            raise TestStopped("Insulation test NG")
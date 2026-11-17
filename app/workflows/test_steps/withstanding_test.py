from app.workflows.test_steps.base_step import BaseTestStep
from app.core.exceptions import TestStopped


class WithstandingTestStep(BaseTestStep):

    step_id = "withstanding_test"
    name = "Withstanding Test"

    def __init__(self, instrument_service):
        super().__init__()
        self.instrument_service = instrument_service

    def execute(self, context):

        context["hardware_test_started"] = True

        measurement = self.instrument_service.run_withstanding_test(
            context["model"],
            context["product_configuration"]
        )

        context["withstanding_voltage"] = measurement["value"]
        context["withstanding_normal"] = measurement.get("normal")
        context["withstanding_max"] = measurement.get("maximum")

        if not measurement["passed"]:
            context["judgment"] = "NG"

            raise TestStopped("Withstanding test NG")
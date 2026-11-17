from app.workflows.test_steps.base_step import BaseTestStep
from app.core.exceptions import TestStopped


class VerifyPCRVoltageStep(BaseTestStep):

    step_id = "verify_pcr_voltage"
    name = "Verify PCR2000 Voltage"

    def __init__(self, instrument_service):
        super().__init__()
        self.instrument_service = instrument_service

    def execute(self, context):

        context["hardware_test_started"] = True

        measurement = self.instrument_service.verify_pcr_voltage(
            context["model"],
            context["product_configuration"]
        )

        context["voltage"] = measurement["value"]

        if not measurement["passed"]:
            context["judgment"] = "NG"

            raise TestStopped(
                "PCR2000 voltage verification NG"
            )

        context["judgment"] = "OK"
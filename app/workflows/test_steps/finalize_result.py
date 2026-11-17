from app.workflows.test_steps.base_step import BaseTestStep


class FinalizeResultStep(BaseTestStep):

    step_id = "finalize_result"
    name = "Finalize Test Result"

    def execute(self, context):

        if context.get("judgment") != "OK":
            raise ValueError(
                "Cannot finalize test: judgment is not OK."
            )

        context["test_completed"] = True
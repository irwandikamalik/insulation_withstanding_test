
from app.workflows.test_steps.base_step import BaseTestStep


class TestSequenceEngine:

    def __init__(self, sequence):

        if not sequence:
            raise ValueError(
                "Test sequence cannot be empty."
            )

        if not all(
            isinstance(step, BaseTestStep)
            for step in sequence
        ):
            raise TypeError(
                "Every step must inherit from BaseTestStep."
            )

        step_ids = [
            step.step_id
            for step in sequence
        ]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "Duplicate step_id detected in test sequence."
            )

        self.sequence = tuple(sequence)

    def execute(
        self,
        context,
        progress_callback=None,
        step_callback=None
    ):

        if not isinstance(context, dict):
            raise TypeError(
                "Test context must be a dictionary."
            )

        total_steps = len(self.sequence)

        for index, step in enumerate(
            self.sequence,
            start=1
        ):

            if progress_callback:
                progress_callback(
                    f"Step {index}/{total_steps}: {step.name}"
                )

            if step_callback:
                step_callback(
                    step.step_id,
                    "RUNNING"
                )

            try:

                step.execute(context)

            except Exception:

                if step_callback:
                    step_callback(
                        step.step_id,
                        "FAILED"
                    )

                    # Mark remaining steps as skipped
                    for remaining_step in self.sequence[index:]:

                        step_callback(
                            remaining_step.step_id,
                            "SKIPPED"
                        )

                raise

            else:

                if step_callback:
                    step_callback(
                        step.step_id,
                        "PASSED"
                    )

        if progress_callback:
            progress_callback(
                "Test sequence completed."
            )

        return context

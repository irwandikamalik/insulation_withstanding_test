
from abc import ABC, abstractmethod


class BaseTestStep(ABC):

    step_id = ""
    name = ""

    def __init__(self):
        if not self.step_id:
            raise ValueError(
                "Test step must define a step_id."
            )

        if not self.name:
            raise ValueError(
                "Test step must define a name."
            )

    @abstractmethod
    def execute(self, context):
        """
        Execute one test procedure.

        Args:
            context (dict): Shared test data.

        Returns:
            None
        """
        raise NotImplementedError

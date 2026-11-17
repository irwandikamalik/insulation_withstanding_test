
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot

from app.core.exceptions import TestStopped

from app.workflows.test_sequence import build_test_sequence
from app.workflows.test_sequence_engine import TestSequenceEngine


class TestController(QObject):

    request = Signal(dict)
    progress = Signal(str)
    step_status = Signal(str, str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        instrument_configuration_service,
        instrument_service,
        sequence=None
    ):
        super().__init__()

        self.instrument_configuration_service = (
            instrument_configuration_service
        )

        self.instrument_service = instrument_service

        self.test_sequence = (
            sequence
            if sequence is not None
            else build_test_sequence(
                instrument_configuration_service,
                instrument_service
            )
        )

        self.sequence_engine = TestSequenceEngine(
            self.test_sequence
        )

    @Slot(dict)
    def run(self, test_data):

        now = datetime.now()

        result = dict(test_data)

        result.update({

            "judgment": None,

            "test_date": now.strftime("%Y-%m-%d"),
            "start_time": now.strftime("%H:%M:%S"),
            "finish_time": None,

            "voltage": None,

            "withstanding_voltage": None,
            "withstanding_normal": None,
            "withstanding_max": None,

            "insulation_test": None,
            "insulation_normal": None,
            "insulation_min": None,

            "error_message": None,

            "hardware_test_started": False,
            "test_completed": False,

        })

        try:

            self.sequence_engine.execute(
                result,
                progress_callback=self.progress.emit,
                step_callback=self.step_status.emit
            )

        except TestStopped as error:

            result["judgment"] = "NG"
            result["error_message"] = str(error)

        except Exception as error:

            result["judgment"] = "ERROR"
            result["error_message"] = str(error)

            if result["hardware_test_started"]:

                try:
                    self.instrument_service.safe_shutdown()

                except Exception as shutdown_error:

                    result["error_message"] += (
                        f" | Safe shutdown error: {shutdown_error}"
                    )

        finally:

            if result["judgment"] is None:
                result["judgment"] = "ERROR"

            result["finish_time"] = (
                datetime.now().strftime("%H:%M:%S")
            )

            self.completed.emit(result)

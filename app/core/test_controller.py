
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot

from app.core.exceptions import TestStopped


class TestController(QObject):
    request = Signal(dict)
    progress = Signal(str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        instrument_configuration_service,
        instrument_service
    ):
        super().__init__()

        self.instrument_configuration_service = (
            instrument_configuration_service
        )

        self.instrument_service = instrument_service

    @Slot(dict)
    def run(self, test_data):
        result = dict(test_data)

        result.update({
            "judgment": "ERROR",
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": datetime.now().strftime("%H:%M:%S"),
            "finish_time": None,
            "voltage": None,
            "withstanding_voltage": None,
            "withstanding_normal": None,
            "withstanding_max": None,
            "insulation_test": None,
            "insulation_normal": None,
            "insulation_min": None,
            "error_message": None,
        })

        try:
            self.progress.emit(
                "Checking instrument configuration..."
            )

            product_configuration = result["product_configuration"]

            self.instrument_configuration_service.validate_configuration(
                product_configuration
            )

            self.progress.emit("Running insulation test...")

            insulation = self.instrument_service.run_insulation_test(
                result["model"],
                product_configuration
            )

            result["insulation_test"] = insulation["value"]
            result["insulation_normal"] = insulation.get("normal")
            result["insulation_min"] = insulation.get("minimum")

            if not insulation["passed"]:
                result["judgment"] = "NG"
                raise TestStopped("Insulation test NG")

            self.progress.emit("Running withstanding test...")

            withstand = self.instrument_service.run_withstanding_test(
                result["model"],
                product_configuration
            )

            result["withstanding_voltage"] = withstand["value"]
            result["withstanding_normal"] = withstand.get("normal")
            result["withstanding_max"] = withstand.get("maximum")

            if not withstand["passed"]:
                result["judgment"] = "NG"
                raise TestStopped("Withstanding test NG")

            self.progress.emit(
                "Verifying PCR2000 output voltage..."
            )

            voltage = self.instrument_service.verify_pcr_voltage(
                result["model"],
                product_configuration
            )

            result["voltage"] = voltage["value"]

            if not voltage["passed"]:
                result["judgment"] = "NG"
                raise TestStopped("PCR2000 voltage verification NG")

            result["judgment"] = "OK"

        except TestStopped as error:
            result["error_message"] = str(error)

        except Exception as error:
            result["judgment"] = "ERROR"
            result["error_message"] = str(error)

            try:
                self.instrument_service.safe_shutdown()

            except Exception as shutdown_error:
                result["error_message"] += (
                    f" | Safe shutdown error: {shutdown_error}"
                )

        finally:
            result["finish_time"] = datetime.now().strftime("%H:%M:%S")
            self.completed.emit(result)

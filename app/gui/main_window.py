from pathlib import Path

from PySide6.QtCore import Slot, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QMessageBox
)

from app.database import (
    OperatorDatabase,
    InstrumentDatabase,
    ProductConfigurationDatabase,
    TestResultDatabase,
)

from app.hardware.instrument_service import InstrumentService
from app.instruments.instrument_configuration_service import (
    InstrumentConfigurationService,
)
from app.core.test_controller import TestController

from app.ui.dialogs.operator_management_dialog import OperatorManagementDialog
from app.ui.dialogs.instrument_management_dialog import InstrumentManagementDialog
from app.ui.dialogs.product_configuration_dialog import ProductTestConfigurationDialog
from app.ui.dialogs.recent_results_dialog import RecentResultsDialog
from app.ui.widgets.header_widget import HeaderWidget
from app.ui.widgets.operator_product_widget import OperatorProductWidget
from app.ui.widgets.tester_widget import TesterWidget
from app.config import (
    APP_TITLE,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    HARDWARE_INTEGRATION_READY
)

# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(
            WINDOW_MIN_WIDTH,
            WINDOW_MIN_HEIGHT,
        )
        self.operator_db = OperatorDatabase()
        self.instrument_db = InstrumentDatabase()
        self.product_config_db = ProductConfigurationDatabase()
        self.result_db = TestResultDatabase()
        self.instrument_configuration_service = (
            InstrumentConfigurationService(self.instrument_db)
        )

        self.instrument_service = InstrumentService()

        self.test_thread = None
        self.test_worker = None
        self.operator_logged_in = False

        self.setup_ui()
        self.load_stylesheet()
        self.create_menu_bar()
        self.connect_signals()


    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)

        self.header_widget = HeaderWidget()
        self.status_label = self.header_widget.status_label
        layout.addWidget(self.header_widget)

        self.input_widget = OperatorProductWidget(
            self.product_config_db
        )

        # Alias untuk mempertahankan kompatibilitas
        # dengan method-method MainWindow yang sudah ada.
        self.operatorid_input = self.input_widget.operatorid_input
        self.operatorname_input = self.input_widget.operatorname_input
        self.logout_button = self.input_widget.logout_button

        self.model_input = self.input_widget.model_input
        self.historytag_input = self.input_widget.historytag_input
        self.doortop_input = self.input_widget.doortop_input
        self.doorbot_input = self.input_widget.doorbot_input

        layout.addWidget(self.input_widget)



        self.tester_widget = TesterWidget()
        self.insulation_values = (
            self.tester_widget.insulation_values
        )

        self.withstanding_values = (
            self.tester_widget.withstanding_values
        )
        self.start_button = self.tester_widget.start_button
        layout.addWidget(self.tester_widget, 1)

        self.setCentralWidget(central)

    def create_menu_bar(self):
        menu = self.menuBar().addMenu("Settings")

        operator_action = QAction("Manage Operator List", self)
        operator_action.triggered.connect(
            self.open_operator_management
        )
        menu.addAction(operator_action)

        menu.addSeparator()

        instrument_action = QAction("Manage Instrument", self)
        instrument_action.triggered.connect(
            self.open_instrument_management
        )
        menu.addAction(instrument_action)

        product_config_action = QAction(
            "Manage Product Test Configuration", self
        )
        product_config_action.triggered.connect(
            self.open_product_configuration
        )
        menu.addAction(product_config_action)

        menu.addSeparator()

        history_action = QAction("Recent Test Results", self)
        history_action.triggered.connect(
            self.show_recent_results
        )
        menu.addAction(history_action)
        
    def load_stylesheet(self):

        project_dir = Path(__file__).resolve().parents[2]

        stylesheet_path = (
            project_dir
            / "app"
            / "ui"
            / "styles"
            / "main_window.qss"
        )

        try:
            with open(stylesheet_path, "r", encoding="utf-8") as file:
                stylesheet = file.read()

            self.setStyleSheet(stylesheet)

        except FileNotFoundError:
            print(
                f"WARNING: Stylesheet not found: {stylesheet_path}"
            )

    # --------------------------------------------------------
    # SIGNALS AND INPUT WORKFLOW
    # --------------------------------------------------------

    def connect_signals(self):

        # Operator & Product Widget Signals
        self.input_widget.operator_submitted.connect(
            self.lookup_operator
        )

        self.input_widget.logout_requested.connect(
            self.logout_operator
        )

        self.input_widget.model_changed.connect(
            self.on_model_changed
        )

        self.input_widget.history_tag_submitted.connect(
            self.validate_history_tag
        )

        self.input_widget.door_top_submitted.connect(
            self.focus_door_bottom
        )

        self.input_widget.door_bottom_submitted.connect(
            self.focus_start_button
        )

        # Tester Controls
        self.start_button.clicked.connect(
            self.start_test
        )

    def lookup_operator(self):
        if self.operator_logged_in:
            return

        operator_id = self.operatorid_input.text().strip()
        if not operator_id:
            return

        operator = self.operator_db.get_operator(operator_id)
        if operator is None:
            QMessageBox.warning(
                self, "Invalid Operator",
                f"Operator ID '{operator_id}' was not found."
            )
            self.operatorid_input.clear()
            self.operatorid_input.setFocus()
            return

        _, operator_name = operator
        self.operatorname_input.setText(operator_name)
        self.operatorid_input.setReadOnly(True)
        self.operator_logged_in = True
        self.logout_button.setEnabled(True)
        self.model_input.setFocus()
        self.update_start_button()

    def logout_operator(self):
        if self.test_thread and self.test_thread.isRunning():
            QMessageBox.warning(
                self, "Test Running",
                "Cannot logout while a test is running."
            )
            return

        answer = QMessageBox.question(
            self, "Logout Operator", "Logout current operator?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.operatorid_input.clear()
        self.operatorname_input.clear()
        self.operatorid_input.setReadOnly(False)
        self.operator_logged_in = False
        self.logout_button.setEnabled(False)
        self.clear_product_inputs()
        self.operatorid_input.setFocus()
        self.update_start_button()

    def on_model_changed(self):
        self.historytag_input.clear()
        self.update_start_button()

    def validate_history_tag(self):
        product_model_id = self.model_input.currentData()
        tag = self.historytag_input.text().strip()

        if not product_model_id:
            QMessageBox.warning(self, "Select Model", "Select model before scanning History Tag.")
            self.model_input.setFocus()
            return

        if not tag:
            return

        product = self.product_config_db.get_product_model(product_model_id)
        model = product[1] if product else ""
        expected_prefix = product[2] if product else ""
        if not expected_prefix:
            QMessageBox.warning(
                self, "Model Prefix Missing",
                f"History Tag prefix for model '{model}' has not been configured. "
                "Open Settings > Manage Product Test Configuration."
            )
            self.model_input.setFocus()
            return

        if not tag.startswith(expected_prefix):
            QMessageBox.warning(
                self, "History Tag Mismatch",
                f"History Tag does not match model {model}.\n"
                f"Expected prefix: {expected_prefix}"
            )
            self.historytag_input.clear()
            self.historytag_input.setFocus()
            return

        self.doortop_input.setFocus()
        self.update_start_button()

    def focus_door_bottom(self):
        if self.doortop_input.text().strip():
            self.doorbot_input.setFocus()
        else:
            self.doortop_input.setFocus()

    def focus_start_button(self):
        if self.doorbot_input.text().strip():
            self.start_button.setFocus()
        else:
            self.doorbot_input.setFocus()
        self.update_start_button()

    def clear_product_inputs(self):
        self.model_input.setCurrentIndex(0)
        self.historytag_input.clear()
        self.doortop_input.clear()
        self.doorbot_input.clear()

    def update_start_button(self):
        valid = (
            self.operator_logged_in
            and bool(self.model_input.currentData())
            and bool(self.historytag_input.text().strip())
            and bool(self.doortop_input.text().strip())
            and bool(self.doorbot_input.text().strip())
        )
        if self.test_thread and self.test_thread.isRunning():
            valid = False
        self.start_button.setEnabled(valid)

    # --------------------------------------------------------
    # TEST SEQUENCE
    # --------------------------------------------------------

    def start_test(self):
        if not self.operator_logged_in:
            QMessageBox.warning(self, "Operator Required", "Login operator first.")
            self.operatorid_input.setFocus()
            return

        product_model_id = self.model_input.currentData()
        product = self.product_config_db.get_product_model(product_model_id) if product_model_id else None
        model = product[1] if product else None
        history_tag = self.historytag_input.text().strip()
        door_top = self.doortop_input.text().strip()
        door_bottom = self.doorbot_input.text().strip()

        if not model or not history_tag or not door_top or not door_bottom:
            QMessageBox.warning(
                self, "Incomplete Input",
                "Complete model and all barcode inputs first."
            )
            return

        expected_prefix = product[2] if product else ""
        if not expected_prefix or not history_tag.startswith(expected_prefix):
            QMessageBox.warning(
                self, "Invalid History Tag",
                "History Tag has not passed model-prefix validation."
            )
            self.historytag_input.setFocus()
            return

        if not HARDWARE_INTEGRATION_READY:
            QMessageBox.critical(
                self,
                "Hardware Integration Not Ready",
                "The input workflow is valid, but real testing is disabled.\n\n"
                "Implement and verify WT310E/PCR2000/TOS9200 drivers, "
                "test limits, interlocks and safe-discharge procedure before "
                "enabling high-voltage testing."
            )
            return

        product_configuration = self.product_config_db.get_complete_configuration(
            product_model_id
        )
        test_data = {
            "product_model_id": product_model_id,
            "product_configuration": product_configuration,
            "operator_id": self.operatorid_input.text().strip(),
            "operator_name": self.operatorname_input.text().strip(),
            "model": model,
            "history_tag": history_tag,
            "door_top": door_top,
            "door_bottom": door_bottom,
        }
        self.start_test_worker(test_data)

    def start_test_worker(self, test_data):
        self.start_button.setEnabled(False)
        self.status_label.setText("●  TESTING")

        self.test_thread = QThread(self)
        self.test_worker = TestController(
            self.instrument_configuration_service,
            self.instrument_service
        )
        self.test_worker.request.connect(self.test_worker.run)
        self.test_worker.moveToThread(self.test_thread)

        self.test_worker.progress.connect(self.on_test_progress)
        self.test_worker.completed.connect(self.on_test_completed)
        self.test_worker.completed.connect(self.test_thread.quit)
        self.test_worker.completed.connect(self.test_worker.deleteLater)
        self.test_thread.finished.connect(self.test_thread.deleteLater)
        self.test_thread.finished.connect(self.on_test_thread_finished)
        self.test_thread.start()
        self.test_worker.request.emit(test_data)

    @Slot(str)
    def on_test_progress(self, message):
        self.status_label.setText(f"●  {message.upper()}")

    @Slot(dict)
    def on_test_completed(self, result):
        try:
            self.result_db.save_result(result)
        except Exception as error:
            QMessageBox.critical(
                self, "Database Error",
                f"Test finished but result could not be saved:\n{error}"
            )
            self.status_label.setText("●  DATABASE ERROR")
            return

        judgment = result["judgment"]
        if judgment == "OK":
            self.status_label.setText("●  PASS")
            QMessageBox.information(self, "Test Complete", "Product judgment: OK")
            self.clear_product_inputs()
        elif judgment == "NG":
            self.status_label.setText("●  FAIL")
            QMessageBox.warning(
                self, "Test NG",
                f"Product judgment: NG\n{result.get('error_message') or ''}"
            )
            self.clear_product_inputs()
        else:
            self.status_label.setText("●  ERROR")
            QMessageBox.critical(
                self, "Test Error",
                f"Test could not be completed.\n"
                f"{result.get('error_message') or 'Unknown error'}"
            )
            # Preserve scanned product data on ERROR for investigation.

        self.update_start_button()

    def on_test_thread_finished(self):
        self.test_thread = None
        self.test_worker = None
        self.status_label.setText("●  READY")
        self.update_start_button()

    # --------------------------------------------------------
    # DIALOGS AND HISTORY
    # --------------------------------------------------------

    def open_operator_management(self):
        dialog = OperatorManagementDialog(self.operator_db, self)
        dialog.exec()

    def open_instrument_management(self):
        dialog = InstrumentManagementDialog(self.instrument_db, self)
        dialog.exec()

    def open_product_configuration(self):
        dialog = ProductTestConfigurationDialog(
            self.product_config_db, self
        )
        dialog.exec()

        current_id = self.model_input.currentData()

        self.model_input.blockSignals(True)
        self.model_input.clear()
        self.model_input.addItem("Select Model", None)

        for product in self.product_config_db.get_product_models():
            product_id, model_name, _prefix, _enabled = product
            self.model_input.addItem(model_name, product_id)

        restored_index = self.model_input.findData(current_id)
        self.model_input.setCurrentIndex(
            restored_index if restored_index >= 0 else 0
        )

        self.model_input.blockSignals(False)
        self.update_start_button()

    def show_recent_results(self):
        rows = self.result_db.get_recent_results()

        dialog = RecentResultsDialog(rows, self)
        dialog.exec()

    def closeEvent(self, event):
        if self.test_thread and self.test_thread.isRunning():
            QMessageBox.warning(
                self, "Test Running",
                "Cannot close application while a test is running."
            )
            event.ignore()
            return
        event.accept()
import sys
from datetime import datetime

from PySide6.QtCore import Qt, Slot, QThread
from PySide6.QtGui import ( 
    QAction, QShortcut, QKeySequence
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QSizePolicy, QFrame, QDialog, QDialogButtonBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QSpinBox, QInputDialog,QScrollArea,
    QWidget
)

from app.database import (
    OperatorDatabase,
    InstrumentDatabase,
    ProductConfigurationDatabase,
    TestResultDatabase
)
from app.hardware.instrument_service import InstrumentService
from app.core.test_controller import TestController
from app.ui.dialogs.operator_management_dialog import OperatorManagementDialog
from app.ui.dialogs.instrument_management_dialog import InstrumentManagementDialog
from app.ui.dialogs.product_configuration_dialog import ProductTestConfigurationDialog
from app.ui.widgets.header_widget import HeaderWidget
from app.ui.widgets.operator_product_widget import OperatorProductWidget
from app.ui.widgets.tester_widget import TesterWidget
from app.ui.dialogs.recent_results_dialog import RecentResultsDialog

# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Insulation & Withstanding Tester"

# Set to True only after implementing and verifying the actual
# instrument drivers, SCPI commands, interlocks and safety sequence.
HARDWARE_INTEGRATION_READY = False


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 750)

        self.operator_db = OperatorDatabase()
        self.instrument_db = InstrumentDatabase()
        self.product_config_db = ProductConfigurationDatabase()
        self.result_db = TestResultDatabase()
        self.instrument_service = InstrumentService(self.instrument_db)

        self.test_thread = None
        self.test_worker = None
        self.operator_logged_in = False

        self.mainUI()
        self.setStyleSheet(self.stylesheet())
        self.createMenuBar()
        self.connect_signals()
        self.showMaximized()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def mainUI(self):
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

    def mainInputUI(self):
        group = QGroupBox("Operator & Product Information")
        layout = QHBoxLayout(group)
        layout.setSpacing(15)

        operator_group = QGroupBox("Operator")
        operator_form = QFormLayout(operator_group)

        self.operatorid_input = QLineEdit()
        self.operatorname_input = QLineEdit()
        self.operatorid_input.setPlaceholderText("Scan Operator ID and press Enter")
        self.operatorname_input.setReadOnly(True)
        self.operatorname_input.setPlaceholderText("Operator Name")
        self.logout_button = QPushButton("Logout")
        self.logout_button.setEnabled(False)

        operator_form.addRow("Operator ID:", self.operatorid_input)
        operator_form.addRow("Name:", self.operatorname_input)
        operator_form.addRow(self.logout_button)

        product_group = QGroupBox("Product Barcode")
        product_form = QFormLayout(product_group)

        self.model_input = QComboBox()
        self.model_input.addItem("Select Model", None)
        for product in self.product_config_db.get_product_models():
            product_id, model_name, _prefix, _enabled = product
            self.model_input.addItem(model_name, product_id)

        self.historytag_input = QLineEdit()
        self.doortop_input = QLineEdit()
        self.doorbot_input = QLineEdit()

        self.historytag_input.setPlaceholderText("Scan History Tag")
        self.doortop_input.setPlaceholderText("Scan Door Top Barcode")
        self.doorbot_input.setPlaceholderText("Scan Door Bottom Barcode")

        product_form.addRow("Model:", self.model_input)
        product_form.addRow("History Tag:", self.historytag_input)
        product_form.addRow("Door Top:", self.doortop_input)
        product_form.addRow("Door Bottom:", self.doorbot_input)

        operator_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        product_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(operator_group, 1)
        layout.addWidget(product_group, 2)
        group.setMaximumHeight(330)
        return group

    def createMenuBar(self):
        menu = self.menuBar().addMenu("Settings")

        operator_action = QAction("Manage Operator List", self)
        operator_action.triggered.connect(self.openOperatorManagement)
        menu.addAction(operator_action)

        menu.addSeparator()

        instrument_action = QAction("Manage Instrument", self)
        instrument_action.triggered.connect(self.openInstrumentManagement)
        menu.addAction(instrument_action)

        product_config_action = QAction("Manage Product Test Configuration", self)
        product_config_action.triggered.connect(self.openProductConfiguration)
        menu.addAction(product_config_action)

        menu.addSeparator()

        history_action = QAction("Recent Test Results", self)
        history_action.triggered.connect(self.showRecentResults)
        menu.addAction(history_action)

    # --------------------------------------------------------
    # SIGNALS AND INPUT WORKFLOW
    # --------------------------------------------------------

    def connect_signals(self):

        # Operator & Product Widget Signals
        self.input_widget.operator_submitted.connect(
            self.lookupOperator
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

    def lookupOperator(self):
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
        self.test_worker = TestController(self.instrument_service)
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

    def openOperatorManagement(self):
        dialog = OperatorManagementDialog(self.operator_db, self)
        dialog.exec()

    def openInstrumentManagement(self):
        dialog = InstrumentManagementDialog(self.instrument_db, self)
        dialog.exec()

    def openProductConfiguration(self):
        dialog = ProductTestConfigurationDialog(self.product_config_db, self)
        dialog.exec()
        current_id = self.model_input.currentData()
        self.model_input.blockSignals(True)
        self.model_input.clear()
        self.model_input.addItem("Select Model", None)
        for product in self.product_config_db.get_product_models():
            product_id, model_name, _prefix, _enabled = product
            self.model_input.addItem(model_name, product_id)
        restored_index = self.model_input.findData(current_id)
        self.model_input.setCurrentIndex(restored_index if restored_index >= 0 else 0)
        self.model_input.blockSignals(False)
        self.update_start_button()

    def showRecentResults(self):

        rows = self.result_db.get_recent_results()

        dialog = RecentResultsDialog(
            rows,
            self
        )

        dialog.exec()

        
    # --------------------------------------------------------
    # STYLESHEET
    # --------------------------------------------------------

    def stylesheet(self):
        return """
        QMainWindow { background-color: #EAF0F8; }
        QWidget {
            font-family: "Segoe UI";
            font-size: 14px;
            color: #172B4D;
        }
        QFrame#header {
            background-color: #123B68;
            border-radius: 12px;
        }
        QLabel#headerTitle {
            color: white;
            font-size: 30px;
            font-weight: bold;
        }
        QLabel#statusLabel {
            color: #4ADE80;
            font-size: 18px;
            font-weight: bold;
        }
        QGroupBox {
            background-color: #FFFFFF;
            border: 2px solid #C6D4E5;
            border-radius: 10px;
            margin-top: 22px;
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 15px;
            padding: 0 8px;
            color: #174A7E;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #F8FAFD;
            border: 2px solid #C5D3E4;
            border-radius: 6px;
            padding: 7px 9px;
            min-height: 27px;
            font-size: 15px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #2588D8;
            background-color: white;
        }
        QLineEdit:read-only { background-color: #E8EDF4; color: #64748B; }
        QLabel#digitalValue {
            background-color: #142F49;
            color: #A8F5B7;
            border: 2px solid #36536C;
            border-radius: 8px;
            font-family: "Consolas";
            font-size: 28px;
            font-weight: bold;
        }
        QGroupBox#insulationGroup { border: 2px solid #16A36A; }
        QGroupBox#insulationGroup::title { color: #07864E; }
        QGroupBox#withstandingGroup { border: 2px solid #5540B8; }
        QGroupBox#withstandingGroup::title { color: #5540B8; }
        QPushButton {
            background-color: #315B82;
            border: none;
            border-radius: 8px;
            color: white;
            padding: 9px 16px;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #24496D; }
        QPushButton:disabled { background-color: #AAB7C4; color: #E9EEF3; }
        QPushButton#startButton {
            background-color: #119B5D;
            font-size: 23px;
        }
        QPushButton#startButton:hover { background-color: #0D7F4B; }
        QPushButton#startButton:disabled { background-color: #AAB7C4; }
        """

    def closeEvent(self, event):
        if self.test_thread and self.test_thread.isRunning():
            QMessageBox.warning(
                self, "Test Running",
                "Cannot close application while a test is running."
            )
            event.ignore()
            return
        event.accept()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())


import sqlite3

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
)


class InstrumentFormDialog(QDialog):
    """Stores physical instrument identity and communication settings only."""

    def __init__(self, database, parent=None, instrument=None):
        super().__init__(parent)
        self.database = database
        self.instrument = instrument
        self.setWindowTitle("Instrument Communication Configuration")
        self.setMinimumWidth(520)
        self.setup_ui()
        if instrument:
            self.load_instrument()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        self.model_input = QComboBox()
        self.model_input.addItems(self.database.INSTRUMENT_MODELS.keys())
        form.addRow("Instrument:", self.model_input)

        self.interface_input = QComboBox()
        self.interface_input.addItem("Select Interface", "")
        for interface in self.database.INTERFACES:
            self.interface_input.addItem(interface, interface)
        form.addRow("Communication Interface:", self.interface_input)

        self.resource_input = QLineEdit()
        self.resource_input.setPlaceholderText(
            "VISA resource, e.g. USB0::... / GPIB0::... / TCPIP0::..."
        )
        form.addRow("Resource Name:", self.resource_input)

        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(100, 120000)
        self.timeout_input.setValue(5000)
        self.timeout_input.setSuffix(" ms")
        form.addRow("Timeout:", self.timeout_input)

        self.enabled_input = QComboBox()
        self.enabled_input.addItem("Enabled", 1)
        self.enabled_input.addItem("Disabled", 0)
        form.addRow("Status:", self.enabled_input)

        main_layout.addLayout(form)
        note = QLabel(
            "Product-specific test parameters are configured separately in "
            "Settings > Manage Product Test Configuration."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #64748B; font-size: 12px;")
        main_layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_form)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def load_instrument(self):
        instrument_id, model, interface, resource, timeout, enabled = self.instrument
        self.model_input.setCurrentText(model)
        interface_index = self.interface_input.findData(interface)
        self.interface_input.setCurrentIndex(max(0, interface_index))
        self.resource_input.setText(resource or "")
        self.timeout_input.setValue(timeout)
        enabled_index = self.enabled_input.findData(enabled)
        self.enabled_input.setCurrentIndex(max(0, enabled_index))

    def validate_form(self):
        model = self.model_input.currentText()
        interface = self.interface_input.currentData()
        resource = self.resource_input.text().strip()

        if not interface:
            QMessageBox.warning(self, "Invalid Configuration", "Select an interface.")
            return
        if not resource:
            QMessageBox.warning(self, "Invalid Configuration", "Resource name is required.")
            return

        instrument_id = self.instrument[0] if self.instrument else None
        try:
            self.database.save_instrument(
                instrument_id,
                model,
                interface,
                resource,
                self.timeout_input.value(),
                self.enabled_input.currentData(),
                {}
            )
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self, "Duplicate Instrument",
                f"An instrument with model {model} already exists."
            )
            return
        self.accept()

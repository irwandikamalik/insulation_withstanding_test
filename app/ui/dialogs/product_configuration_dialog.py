import sqlite3

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QScrollArea,
    QInputDialog,
    QMessageBox,
    QWidget,
)

from app.database import InstrumentDatabase


class ProductTestConfigurationDialog(QDialog):
    """Edit test settings for a selected product and instrument model."""

    def __init__(self, product_db, parent=None):
        super().__init__(parent)
        self.product_db = product_db
        self.setting_inputs = {}
        self.current_product_id = None
        self.setWindowTitle("Manage Product Test Configuration")
        self.setMinimumSize(650, 570)
        self.setup_ui()
        self.load_product_models()

    def setup_ui(self):
        root = QVBoxLayout(self)
        product_group = QGroupBox("Product Model")
        product_form = QFormLayout(product_group)
        self.product_combo = QComboBox()
        self.product_name_input = QLineEdit()
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("History Tag prefix, e.g. *13J")
        self.enabled_combo = QComboBox()
        self.enabled_combo.addItem("Enabled", 1)
        self.enabled_combo.addItem("Disabled", 0)
        product_form.addRow("Select Product:", self.product_combo)
        product_form.addRow("Model Name:", self.product_name_input)
        product_form.addRow("History Tag Prefix:", self.prefix_input)
        product_form.addRow("Status:", self.enabled_combo)
        root.addWidget(product_group)

        model_buttons = QHBoxLayout()
        self.new_model_button = QPushButton("New Product Model")
        self.save_model_button = QPushButton("Save Product Model")
        model_buttons.addWidget(self.new_model_button)
        model_buttons.addWidget(self.save_model_button)
        model_buttons.addStretch()
        root.addLayout(model_buttons)

        setting_group = QGroupBox(
            "Product-specific Instrument Parameters"
        )
        setting_layout = QVBoxLayout(setting_group)
        instrument_row = QHBoxLayout()
        instrument_row.addWidget(QLabel("Instrument:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems(
            InstrumentDatabase.INSTRUMENT_MODELS.keys()
        )
        instrument_row.addWidget(self.instrument_combo, 1)
        setting_layout.addLayout(instrument_row)
        self.settings_scroll = QScrollArea()
        self.settings_scroll.setWidgetResizable(True)
        self.settings_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.settings_widget = QWidget()
        self.settings_form = QFormLayout(
            self.settings_widget
        )
        self.settings_scroll.setWidget(
            self.settings_widget
        )
        setting_layout.addWidget(
            self.settings_scroll,
            1
        )
        root.addWidget(setting_group, 1)

        action_row = QHBoxLayout()
        self.save_settings_button = QPushButton("Save Instrument Parameters")
        close_button = QPushButton("Close")
        action_row.addWidget(self.save_settings_button)
        action_row.addStretch()
        action_row.addWidget(close_button)
        root.addLayout(action_row)

        self.product_combo.currentIndexChanged.connect(self.load_selected_product)
        self.instrument_combo.currentTextChanged.connect(self.load_selected_instrument_settings)
        self.new_model_button.clicked.connect(self.create_product_model)
        self.save_model_button.clicked.connect(self.save_product_model)
        self.save_settings_button.clicked.connect(self.save_instrument_settings)
        close_button.clicked.connect(self.accept)

    def load_product_models(self, select_id=None):
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for product in self.product_db.get_product_models(enabled_only=False):
            product_id, name, prefix, enabled = product
            self.product_combo.addItem(
                f"{name}{'' if enabled else ' (Disabled)'}", product_id
            )
        if select_id is not None:
            index = self.product_combo.findData(select_id)
            if index >= 0:
                self.product_combo.setCurrentIndex(index)
        self.product_combo.blockSignals(False)
        self.load_selected_product()

    def load_selected_product(self):
        product_id = self.product_combo.currentData()
        self.current_product_id = product_id
        if product_id is None:
            self.product_name_input.clear()
            self.prefix_input.clear()
            return
        product = self.product_db.get_product_model(product_id)
        if not product:
            return
        self.product_name_input.setText(product[1])
        self.prefix_input.setText(product[2] or "")
        self.enabled_combo.setCurrentIndex(self.enabled_combo.findData(product[3]))
        self.load_selected_instrument_settings()

    def create_product_model(self):
        name, accepted = QInputDialog.getText(
            self, "New Product Model", "Enter product model name:"
        )
        if not accepted or not name.strip():
            return
        try:
            self.product_db.add_product_model(name)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Model", "This product model already exists.")
            return
        product = self.product_db.get_product_model_by_name(name.strip())
        self.load_product_models(product[0] if product else None)

    def save_product_model(self):
        if self.current_product_id is None:
            QMessageBox.warning(self, "No Product", "Create or select a product model first.")
            return
        name = self.product_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Model", "Product model name is required.")
            return
        try:
            self.product_db.update_product_model(
                self.current_product_id,
                name,
                self.prefix_input.text().strip(),
                self.enabled_combo.currentData()
            )
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Model", "This product model name already exists.")
            return
        self.load_product_models(self.current_product_id)
        QMessageBox.information(self, "Saved", "Product model configuration saved.")

    def load_selected_instrument_settings(self):
        while self.settings_form.rowCount():
            self.settings_form.removeRow(0)
        self.setting_inputs.clear()
        instrument_model = self.instrument_combo.currentText()
        fields = InstrumentDatabase.INSTRUMENT_MODELS[instrument_model]
        for key, label in fields:
            edit = QLineEdit()
            edit.setPlaceholderText(f"Enter {label} for this product")
            self.settings_form.addRow(f"{label}:", edit)
            self.setting_inputs[key] = edit

        if self.current_product_id is not None:
            values = self.product_db.get_instrument_settings(
                self.current_product_id, instrument_model
            )
            for key, value in values.items():
                if key in self.setting_inputs:
                    self.setting_inputs[key].setText(value)

    def save_instrument_settings(self):
        if self.current_product_id is None:
            QMessageBox.warning(self, "No Product", "Select a product model first.")
            return
        self.save_product_model_silently()
        instrument_model = self.instrument_combo.currentText()
        settings = {
            key: widget.text().strip()
            for key, widget in self.setting_inputs.items()
        }
        self.product_db.save_instrument_settings(
            self.current_product_id, instrument_model, settings
        )
        QMessageBox.information(
            self, "Saved",
            f"{instrument_model} parameters for "
            f"{self.product_name_input.text().strip()} saved."
        )

    def save_product_model_silently(self):
        name = self.product_name_input.text().strip()
        if not name:
            raise ValueError("Product model name is required.")
        self.product_db.update_product_model(
            self.current_product_id,
            name,
            self.prefix_input.text().strip(),
            self.enabled_combo.currentData()
        )
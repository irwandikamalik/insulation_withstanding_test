import sys
import sqlite3
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QSizePolicy, QFrame, QDialog, QDialogButtonBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPlainTextEdit, QInputDialog,QScrollArea,
    QWidget
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Insulation & Withstanding Tester"

# Set to True only after implementing and verifying the actual
# instrument drivers, SCPI commands, interlocks and safety sequence.
HARDWARE_INTEGRATION_READY = False


# ============================================================
# DATABASE BASE
# ============================================================

class DatabaseBase:
    def __init__(self):
        # This file is intended to be saved as app/gui/main_window.py
        # or in the project root. Adjust parents if your location differs.
        current_file = Path(__file__).resolve()
        candidates = [current_file.parent, *current_file.parents]
        project_dir = next(
            (p for p in candidates if (p / "data").exists()),
            current_file.parent
        )
        self.db_dir = project_dir / "data"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / "insulation_tester.db"

    def get_connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


# ============================================================
# OPERATOR DATABASE
# ============================================================

class OperatorDatabase(DatabaseBase):
    def __init__(self):
        super().__init__()
        self.create_table()

    def create_table(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS operators (
                    operator_id TEXT PRIMARY KEY,
                    operator_name TEXT NOT NULL
                )
            """)

    def get_all_operators(self):
        with self.get_connection() as con:
            return con.execute("""
                SELECT operator_id, operator_name
                FROM operators ORDER BY operator_id
            """).fetchall()

    def get_operator(self, operator_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT operator_id, operator_name
                FROM operators WHERE operator_id = ?
            """, (operator_id,)).fetchone()

    def add_operator(self, operator_id, operator_name):
        with self.get_connection() as con:
            con.execute("""
                INSERT INTO operators(operator_id, operator_name)
                VALUES (?, ?)
            """, (operator_id, operator_name))

    def update_operator(self, old_id, new_id, new_name):
        with self.get_connection() as con:
            con.execute("""
                UPDATE operators
                SET operator_id = ?, operator_name = ?
                WHERE operator_id = ?
            """, (new_id, new_name, old_id))

    def delete_operator(self, operator_id):
        with self.get_connection() as con:
            con.execute(
                "DELETE FROM operators WHERE operator_id = ?",
                (operator_id,)
            )


# ============================================================
# INSTRUMENT DATABASE
# ============================================================

class InstrumentDatabase(DatabaseBase):
    INSTRUMENT_MODELS = {
        "WT310E": [
            ("measurement_function", "Measurement Function"),
            ("voltage_range", "Voltage Range"),
            ("current_range", "Current Range"),
            ("frequency_range", "Frequency Range"),
            ("measurement_interval", "Measurement Interval"),
            ("wiring_mode", "Wiring Mode"),
        ],
        "PCR2000": [
            ("output_voltage", "Output Voltage"),
            ("output_frequency", "Output Frequency"),
            ("current_limit", "Current Limit"),
            ("output_mode", "Output Mode"),
            ("output_state", "Output State"),
        ],
        "TOS9200": [
            ("test_mode", "Test Mode"),
            ("test_voltage", "Test Voltage"),
            ("upper_limit", "Upper Limit"),
            ("lower_limit", "Lower Limit"),
            ("test_time", "Test Time"),
            ("ramp_time", "Ramp Time"),
            ("discharge_time", "Discharge Time"),
        ],
    }

    INTERFACES = ["USB", "GPIB", "TCPIP", "Serial"]

    def __init__(self):
        super().__init__()
        self.create_tables()
        self.seed_instruments()

    def create_tables(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS instruments (
                    instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL UNIQUE,
                    interface TEXT,
                    resource_name TEXT,
                    timeout_ms INTEGER NOT NULL DEFAULT 5000,
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS instrument_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_id INTEGER NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    UNIQUE(instrument_id, setting_key),
                    FOREIGN KEY(instrument_id)
                        REFERENCES instruments(instrument_id)
                        ON DELETE CASCADE
                )
            """)

    def seed_instruments(self):
        with self.get_connection() as con:
            for model in self.INSTRUMENT_MODELS:
                con.execute("""
                    INSERT OR IGNORE INTO instruments(model)
                    VALUES (?)
                """, (model,))

    def get_all_instruments(self):
        with self.get_connection() as con:
            return con.execute("""
                SELECT instrument_id, model, interface,
                       resource_name, timeout_ms, enabled
                FROM instruments ORDER BY model
            """).fetchall()

    def get_instrument(self, instrument_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT instrument_id, model, interface,
                       resource_name, timeout_ms, enabled
                FROM instruments WHERE instrument_id = ?
            """, (instrument_id,)).fetchone()

    def get_instrument_settings(self, instrument_id):
        with self.get_connection() as con:
            rows = con.execute("""
                SELECT setting_key, setting_value
                FROM instrument_settings
                WHERE instrument_id = ?
            """, (instrument_id,)).fetchall()
            return dict(rows)

    def save_instrument(
        self, instrument_id, model, interface,
        resource_name, timeout_ms, enabled, settings
    ):
        if model not in self.INSTRUMENT_MODELS:
            raise ValueError("Unsupported instrument model.")

        with self.get_connection() as con:
            if instrument_id is None:
                cursor = con.execute("""
                    INSERT INTO instruments(
                        model, interface, resource_name,
                        timeout_ms, enabled
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    model, interface, resource_name,
                    timeout_ms, enabled
                ))
                instrument_id = cursor.lastrowid
            else:
                con.execute("""
                    UPDATE instruments
                    SET model = ?, interface = ?, resource_name = ?,
                        timeout_ms = ?, enabled = ?
                    WHERE instrument_id = ?
                """, (
                    model, interface, resource_name,
                    timeout_ms, enabled, instrument_id
                ))

            valid_keys = {
                key for key, _ in self.INSTRUMENT_MODELS[model]
            }
            for key, value in settings.items():
                if key in valid_keys:
                    con.execute("""
                        INSERT INTO instrument_settings(
                            instrument_id, setting_key, setting_value
                        ) VALUES (?, ?, ?)
                        ON CONFLICT(instrument_id, setting_key)
                        DO UPDATE SET setting_value = excluded.setting_value
                    """, (instrument_id, key, value))

            if valid_keys:
                placeholders = ",".join("?" for _ in valid_keys)
                con.execute(f"""
                    DELETE FROM instrument_settings
                    WHERE instrument_id = ?
                    AND setting_key NOT IN ({placeholders})
                """, (instrument_id, *valid_keys))

    def delete_instrument(self, instrument_id):
        with self.get_connection() as con:
            con.execute(
                "DELETE FROM instruments WHERE instrument_id = ?",
                (instrument_id,)
            )


# ============================================================
# PRODUCT TEST CONFIGURATION DATABASE
# ============================================================

class ProductConfigurationDatabase(DatabaseBase):
    """Stores test parameters per product model and instrument type."""

    def __init__(self):
        super().__init__()
        self.create_tables()
        self.seed_product_models()

    def create_tables(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS product_models (
                    product_model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL UNIQUE,
                    history_prefix TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS product_instrument_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_model_id INTEGER NOT NULL,
                    instrument_model TEXT NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL DEFAULT '',
                    UNIQUE(product_model_id, instrument_model, setting_key),
                    FOREIGN KEY(product_model_id)
                        REFERENCES product_models(product_model_id)
                        ON DELETE CASCADE
                )
            """)

    def seed_product_models(self):
        # Europe prefix is intentionally blank: enter the real prefix in
        # Manage Product Test Configuration rather than guessing it.
        with self.get_connection() as con:
            con.execute("""
                INSERT OR IGNORE INTO product_models(model_name, history_prefix)
                VALUES ('Japan', '*13J')
            """)
            con.execute("""
                INSERT OR IGNORE INTO product_models(model_name, history_prefix)
                VALUES ('Europe', '')
            """)

    def get_product_models(self, enabled_only=True):
        sql = """
            SELECT product_model_id, model_name, history_prefix, enabled
            FROM product_models
        """
        if enabled_only:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY model_name"
        with self.get_connection() as con:
            return con.execute(sql).fetchall()

    def get_product_model(self, product_model_id):
        with self.get_connection() as con:
            return con.execute("""
                SELECT product_model_id, model_name, history_prefix, enabled
                FROM product_models WHERE product_model_id = ?
            """, (product_model_id,)).fetchone()

    def get_product_model_by_name(self, model_name):
        with self.get_connection() as con:
            return con.execute("""
                SELECT product_model_id, model_name, history_prefix, enabled
                FROM product_models WHERE model_name = ?
            """, (model_name,)).fetchone()

    def add_product_model(self, model_name, history_prefix=''):
        with self.get_connection() as con:
            con.execute("""
                INSERT INTO product_models(model_name, history_prefix)
                VALUES (?, ?)
            """, (model_name.strip(), history_prefix.strip()))

    def update_product_model(self, product_model_id, model_name, history_prefix, enabled):
        with self.get_connection() as con:
            con.execute("""
                UPDATE product_models
                SET model_name = ?, history_prefix = ?, enabled = ?
                WHERE product_model_id = ?
            """, (model_name.strip(), history_prefix.strip(), enabled, product_model_id))

    def save_instrument_settings(self, product_model_id, instrument_model, settings):
        valid_keys = {
            key for key, _ in InstrumentDatabase.INSTRUMENT_MODELS[instrument_model]
        }
        with self.get_connection() as con:
            for key, value in settings.items():
                if key not in valid_keys:
                    continue
                con.execute("""
                    INSERT INTO product_instrument_settings(
                        product_model_id, instrument_model, setting_key, setting_value
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(product_model_id, instrument_model, setting_key)
                    DO UPDATE SET setting_value = excluded.setting_value
                """, (product_model_id, instrument_model, key, str(value).strip()))

    def get_instrument_settings(self, product_model_id, instrument_model):
        with self.get_connection() as con:
            rows = con.execute("""
                SELECT setting_key, setting_value
                FROM product_instrument_settings
                WHERE product_model_id = ? AND instrument_model = ?
            """, (product_model_id, instrument_model)).fetchall()
            return dict(rows)

    def get_complete_configuration(self, product_model_id):
        model = self.get_product_model(product_model_id)
        if not model:
            raise ValueError("Product model not found.")
        config = {
            "product_model_id": model[0],
            "model_name": model[1],
            "history_prefix": model[2],
            "instruments": {}
        }
        for instrument_model in InstrumentDatabase.INSTRUMENT_MODELS:
            config["instruments"][instrument_model] = (
                self.get_instrument_settings(product_model_id, instrument_model)
            )
        return config


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


# ============================================================
# TEST RESULT DATABASE
# ============================================================

class TestResultDatabase(DatabaseBase):
    def __init__(self):
        super().__init__()
        self.create_table()

    def create_table(self):
        with self.get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    judgment TEXT NOT NULL,
                    test_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    finish_time TEXT,
                    operator_id TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    model TEXT NOT NULL,
                    history_tag TEXT NOT NULL,
                    door_top TEXT NOT NULL,
                    door_bottom TEXT NOT NULL,
                    voltage REAL,
                    withstanding_voltage REAL,
                    withstanding_normal REAL,
                    withstanding_max REAL,
                    insulation_test REAL,
                    insulation_normal REAL,
                    insulation_min REAL,
                    error_message TEXT
                )
            """)

    def save_result(self, result):
        columns = [
            "judgment", "test_date", "start_time", "finish_time",
            "operator_id", "operator_name", "model", "history_tag",
            "door_top", "door_bottom", "voltage",
            "withstanding_voltage", "withstanding_normal",
            "withstanding_max", "insulation_test",
            "insulation_normal", "insulation_min", "error_message"
        ]
        placeholders = ",".join("?" for _ in columns)
        sql = (
            f"INSERT INTO test_results ({','.join(columns)}) "
            f"VALUES ({placeholders})"
        )
        with self.get_connection() as con:
            con.execute(sql, tuple(result.get(c) for c in columns))

    def get_recent_results(self, limit=100):
        with self.get_connection() as con:
            return con.execute("""
                SELECT result_id, judgment, test_date, start_time,
                       operator_id, model, history_tag
                FROM test_results
                ORDER BY result_id DESC LIMIT ?
            """, (limit,)).fetchall()


# ============================================================
# OPERATOR FORM AND MANAGEMENT
# ============================================================

class OperatorFormDialog(QDialog):
    def __init__(self, parent=None, operator_id="", operator_name=""):
        super().__init__(parent)
        self.setWindowTitle("Operator Information")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.operator_id_input = QLineEdit(operator_id)
        self.operator_name_input = QLineEdit(operator_name)

        form.addRow("Operator ID:", self.operator_id_input)
        form.addRow("Operator Name:", self.operator_name_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_form)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_form(self):
        if not self.operator_id_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Operator ID is required.")
            return
        if not self.operator_name_input.text().strip():
            QMessageBox.warning(self, "Invalid Input", "Operator name is required.")
            return
        self.accept()

    def get_data(self):
        return (
            self.operator_id_input.text().strip(),
            self.operator_name_input.text().strip()
        )


class OperatorManagementDialog(QDialog):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("Operator Management")
        self.setMinimumSize(650, 420)
        self.setup_ui()
        self.load_operators()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Operator ID", "Operator Name"])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        close_button = QPushButton("Close")
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.delete_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.add_button.clicked.connect(self.add_operator)
        self.edit_button.clicked.connect(self.edit_operator)
        self.delete_button.clicked.connect(self.delete_operator)
        close_button.clicked.connect(self.accept)

    def load_operators(self):
        rows = self.database.get_all_operators()
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def selected_operator(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select an operator first.")
            return None
        return (
            self.table.item(row, 0).text(),
            self.table.item(row, 1).text()
        )

    def add_operator(self):
        dialog = OperatorFormDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.database.add_operator(*dialog.get_data())
            self.load_operators()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate ID", "Operator ID already exists.")

    def edit_operator(self):
        selected = self.selected_operator()
        if not selected:
            return
        old_id, old_name = selected
        dialog = OperatorFormDialog(self, old_id, old_name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            new_id, new_name = dialog.get_data()
            self.database.update_operator(old_id, new_id, new_name)
            self.load_operators()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate ID", "Operator ID already exists.")

    def delete_operator(self):
        selected = self.selected_operator()
        if not selected:
            return
        operator_id, operator_name = selected
        answer = QMessageBox.question(
            self, "Delete Operator",
            f"Delete {operator_name} ({operator_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_operator(operator_id)
            self.load_operators()


# ============================================================
# INSTRUMENT CONFIGURATION FORM
# ============================================================

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


class InstrumentManagementDialog(QDialog):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("Instrument Management")
        self.setMinimumSize(900, 450)
        self.setup_ui()
        self.load_instruments()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Model", "Interface", "Resource Name", "Timeout (ms)", "Status"
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        add_button = QPushButton("Add")
        edit_button = QPushButton("Edit")
        delete_button = QPushButton("Delete")
        close_button = QPushButton("Close")
        for button in (add_button, edit_button, delete_button):
            buttons.addWidget(button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        add_button.clicked.connect(self.add_instrument)
        edit_button.clicked.connect(self.edit_instrument)
        delete_button.clicked.connect(self.delete_instrument)
        close_button.clicked.connect(self.accept)

    def load_instruments(self):
        rows = self.database.get_all_instruments()
        self.table.setRowCount(len(rows))
        for row, data in enumerate(rows):
            instrument_id, model, interface, resource, timeout, enabled = data
            values = [
                model, interface or "-", resource or "-",
                str(timeout), "Enabled" if enabled else "Disabled"
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
            self.table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, instrument_id
            )

    def selected_instrument(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select an instrument first.")
            return None
        instrument_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return self.database.get_instrument(instrument_id)

    def add_instrument(self):
        dialog = InstrumentFormDialog(self.database, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_instruments()

    def edit_instrument(self):
        instrument = self.selected_instrument()
        if not instrument:
            return
        dialog = InstrumentFormDialog(self.database, self, instrument)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_instruments()

    def delete_instrument(self):
        instrument = self.selected_instrument()
        if not instrument:
            return
        instrument_id, model = instrument[0], instrument[1]
        answer = QMessageBox.question(
            self, "Delete Instrument", f"Delete {model}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_instrument(instrument_id)
            self.load_instruments()


# ============================================================
# HARDWARE ADAPTER INTERFACE
# ============================================================

class HardwareIntegrationError(RuntimeError):
    pass


class InstrumentService:
    """
    Safe integration boundary for real instruments.

    Implement and verify the methods below against the exact instrument
    manuals, installed options, wiring and safety procedure before enabling
    HARDWARE_INTEGRATION_READY.

    Never replace these methods with guessed SCPI commands.
    """

    def __init__(self, instrument_database):
        self.instrument_database = instrument_database

    def validate_configuration(self, product_configuration=None):
        rows = self.instrument_database.get_all_instruments()
        enabled = [row for row in rows if row[5]]
        configured_models = {row[1] for row in enabled}

        required = {"WT310E", "PCR2000", "TOS9200"}
        missing = required - configured_models
        if missing:
            raise HardwareIntegrationError(
                "Enabled instrument configuration missing: "
                + ", ".join(sorted(missing))
            )

        for row in enabled:
            _, model, interface, resource, timeout, _ = row
            if not interface or not resource:
                raise HardwareIntegrationError(
                    f"{model} has incomplete communication configuration."
                )

        if product_configuration is not None:
            product_name = product_configuration.get("model_name", "Unknown")
            per_instrument = product_configuration.get("instruments", {})
            for instrument_model, definitions in InstrumentDatabase.INSTRUMENT_MODELS.items():
                values = per_instrument.get(instrument_model, {})
                missing_settings = [
                    key for key, _label in definitions
                    if not str(values.get(key, "")).strip()
                ]
                if missing_settings:
                    raise HardwareIntegrationError(
                        f"Product '{product_name}' has incomplete {instrument_model} "
                        f"settings: {', '.join(missing_settings)}"
                    )

    def run_insulation_test(self, model, product_configuration):
        raise HardwareIntegrationError(
            "TOS9200 insulation driver is not implemented and verified."
        )

    def run_withstanding_test(self, model, product_configuration):
        raise HardwareIntegrationError(
            "TOS9200 withstand driver is not implemented and verified."
        )

    def verify_pcr_voltage(self, model, product_configuration):
        raise HardwareIntegrationError(
            "PCR2000 voltage readback driver and model limits are not configured."
        )

    def safe_shutdown(self):
        # Must be implemented and verified using the instrument manuals.
        # A communication exception does NOT prove that HV output is off.
        pass


# ============================================================
# TEST CONTROLLER
# ============================================================

class TestController(QObject):
    request = Signal(dict)
    progress = Signal(str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, instrument_service):
        super().__init__()
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
            self.progress.emit("Checking instrument configuration...")
            product_configuration = result["product_configuration"]
            self.instrument_service.validate_configuration(product_configuration)

            self.progress.emit("Running insulation test...")
            insulation = self.instrument_service.run_insulation_test(
                result["model"], product_configuration
            )
            result["insulation_test"] = insulation["value"]
            result["insulation_normal"] = insulation.get("normal")
            result["insulation_min"] = insulation.get("minimum")
            if not insulation["passed"]:
                result["judgment"] = "NG"
                raise TestStopped("Insulation test NG")

            self.progress.emit("Running withstanding test...")
            withstand = self.instrument_service.run_withstanding_test(
                result["model"], product_configuration
            )
            result["withstanding_voltage"] = withstand["value"]
            result["withstanding_normal"] = withstand.get("normal")
            result["withstanding_max"] = withstand.get("maximum")
            if not withstand["passed"]:
                result["judgment"] = "NG"
                raise TestStopped("Withstanding test NG")

            self.progress.emit("Verifying PCR2000 output voltage...")
            voltage = self.instrument_service.verify_pcr_voltage(
                result["model"], product_configuration
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


class TestStopped(RuntimeError):
    pass


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

        layout.addWidget(self.headerUI())
        layout.addWidget(self.mainInputUI())
        layout.addWidget(self.testerUI(), 1)
        self.setCentralWidget(central)

    def headerUI(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("⚡  SAFETY TEST")
        title.setObjectName("headerTitle")
        self.status_label = QLabel("●  READY")
        self.status_label.setObjectName("statusLabel")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.status_label)
        return header

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

    def createMeasurementPanel(self, title, measurements, object_name):
        group = QGroupBox(title)
        group.setObjectName(object_name)
        layout = QFormLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        value_labels = {}
        for name, unit in measurements:
            label = QLabel(f"-- {unit}")
            label.setObjectName("digitalValue")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumHeight(60)
            layout.addRow(f"{name}:", label)
            value_labels[name] = label
        group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        return group, value_labels

    def testerUI(self):
        group = QGroupBox("Tester Controls")
        layout = QVBoxLayout(group)

        grid = QGridLayout()
        insulation_group, self.insulation_values = self.createMeasurementPanel(
            "Insulation Test",
            [("Resistance", "MΩ"), ("Voltage", "V"), ("Time", "s")],
            "insulationGroup"
        )
        withstand_group, self.withstanding_values = self.createMeasurementPanel(
            "Withstanding Test",
            [("Voltage", "V"), ("Current", "mA"), ("Time", "s")],
            "withstandingGroup"
        )
        grid.addWidget(insulation_group, 0, 0)
        grid.addWidget(withstand_group, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid, 1)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("▶   START TEST")
        self.start_button.setObjectName("startButton")
        self.start_button.setMinimumHeight(85)
        self.start_button.setEnabled(False)
        buttons.addWidget(self.start_button)
        layout.addLayout(buttons)
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
        self.operatorid_input.returnPressed.connect(self.lookupOperator)
        self.logout_button.clicked.connect(self.logout_operator)
        self.model_input.currentIndexChanged.connect(self.on_model_changed)
        self.historytag_input.returnPressed.connect(self.validate_history_tag)
        self.doortop_input.returnPressed.connect(self.focus_door_bottom)
        self.doorbot_input.returnPressed.connect(self.focus_start_button)
        self.start_button.clicked.connect(self.start_test)

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
        dialog = QDialog(self)
        dialog.setWindowTitle("Recent Test Results")
        dialog.setMinimumSize(900, 450)
        layout = QVBoxLayout(dialog)

        table = QTableWidget(len(rows), 7)
        table.setHorizontalHeaderLabels([
            "ID", "Judgment", "Date", "Time",
            "Operator ID", "Model", "History Tag"
        ])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))

        layout.addWidget(table)
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
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

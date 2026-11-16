from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)

from app.ui.dialogs.instrument_form_dialog import InstrumentFormDialog


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

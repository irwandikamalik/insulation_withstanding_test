import sqlite3

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

from app.ui.dialogs.operator_form_dialog import OperatorFormDialog


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
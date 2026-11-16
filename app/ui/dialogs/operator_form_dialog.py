from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)


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


from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)


class RecentResultsDialog(QDialog):

    def __init__(self, results, parent=None):
        super().__init__(parent)

        self.results = results

        self.setWindowTitle("Recent Test Results")
        self.setMinimumSize(900, 450)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(
            len(self.results),
            7
        )

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Judgment",
            "Date",
            "Time",
            "Operator ID",
            "Model",
            "History Tag"
        ])

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.populate_table()

        layout.addWidget(self.table)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        layout.addWidget(close_button)

    def populate_table(self):
        for row, values in enumerate(self.results):

            for column, value in enumerate(values):

                item = QTableWidgetItem(
                    str(value) if value is not None else "-"
                )

                self.table.setItem(
                    row,
                    column,
                    item
                )

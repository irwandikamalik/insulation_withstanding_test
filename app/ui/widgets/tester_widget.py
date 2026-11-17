
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QProgressBar,
    QFrame,
)
from PySide6.QtGui import QShortcut, QKeySequence


class TesterWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sequence_rows = {}
        self.total_steps = 0
        self.completed_steps = 0

        self.setup_ui()

    def setup_ui(self):

        group = QGroupBox("Tester Controls")
        layout = QVBoxLayout(group)

        # ==========================================
        # MEASUREMENT PANELS
        # ==========================================

        grid = QGridLayout()

        insulation_group, self.insulation_values = (
            self.create_measurement_panel(
                "Insulation Test",
                [
                    ("Resistance", "MΩ"),
                    ("Voltage", "V"),
                    ("Time", "s"),
                ],
                "insulationGroup"
            )
        )

        withstand_group, self.withstanding_values = (
            self.create_measurement_panel(
                "Withstanding Test",
                [
                    ("Voltage", "V"),
                    ("Current", "mA"),
                    ("Time", "s"),
                ],
                "withstandingGroup"
            )
        )

        grid.addWidget(insulation_group, 0, 0)
        grid.addWidget(withstand_group, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid, 3)

        # ==========================================
        # TEST SEQUENCE PANEL
        # ==========================================

        self.sequence_group = QGroupBox("Test Sequence")
        sequence_layout = QVBoxLayout(self.sequence_group)

        # Overall progress
        progress_header = QHBoxLayout()

        self.sequence_progress_label = QLabel("0 / 0 Steps")
        self.sequence_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        progress_header.addWidget(
            QLabel("Overall Progress")
        )
        progress_header.addStretch()
        progress_header.addWidget(
            self.sequence_progress_label
        )

        sequence_layout.addLayout(progress_header)

        self.sequence_progress = QProgressBar()
        self.sequence_progress.setRange(0, 100)
        self.sequence_progress.setValue(0)
        self.sequence_progress.setTextVisible(False)
        self.sequence_progress.setFixedHeight(10)

        sequence_layout.addWidget(self.sequence_progress)

        # Step rows
        self.sequence_list_layout = QVBoxLayout()
        self.sequence_list_layout.setSpacing(8)

        sequence_layout.addLayout(self.sequence_list_layout)

        layout.addWidget(self.sequence_group, 2)

        # ==========================================
        # START TEST BUTTON
        # ==========================================

        buttons = QHBoxLayout()

        self.start_button = QPushButton("▶   START TEST")
        self.start_button.setObjectName("startButton")
        self.start_button.setMinimumHeight(40)
        self.start_button.setEnabled(False)

        self.enter_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Return),
            self.start_button
        )

        self.enter_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.enter_shortcut.activated.connect(
            self.start_button.click
        )

        self.numpad_enter_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Enter),
            self.start_button
        )

        self.numpad_enter_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )

        self.numpad_enter_shortcut.activated.connect(
            self.start_button.click
        )

        buttons.addWidget(self.start_button)
        layout.addLayout(buttons, 1)

        # ==========================================
        # MAIN LAYOUT
        # ==========================================

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(group)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    # ==================================================
    # MEASUREMENT PANEL
    # ==================================================

    def create_measurement_panel(
        self,
        title,
        measurements,
        object_name
    ):

        group = QGroupBox(title)
        group.setObjectName(object_name)

        layout = QFormLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 15, 10, 10)

        value_labels = {}

        for name, unit in measurements:

            label = QLabel(f"-- {unit}")
            label.setObjectName("digitalValue")
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setMinimumHeight(25)

            layout.addRow(f"{name}:", label)

            value_labels[name] = label

        group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        return group, value_labels

    # ==================================================
    # SEQUENCE DISPLAY
    # ==================================================

    def set_sequence(self, sequence):

        self.clear_sequence()

        self.total_steps = len(sequence)
        self.completed_steps = 0

        for index, step in enumerate(sequence, start=1):

            row = QFrame()
            row.setObjectName("sequenceRow")

            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)

            number_label = QLabel(f"{index:02d}")
            number_label.setFixedWidth(30)
            number_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            name_label = QLabel(step.name)

            status_label = QLabel("WAITING")
            status_label.setObjectName("sequenceWaiting")
            status_label.setAlignment(
                Qt.AlignmentFlag.AlignRight
            )
            status_label.setFixedWidth(90)

            self.apply_status_style(
                status_label,
                "WAITING"
            )

            row_layout.addWidget(number_label)
            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(status_label)

            self.sequence_list_layout.addWidget(row)

            self.sequence_rows[step.step_id] = {
                "row": row,
                "name": name_label,
                "status": status_label,
            }

        self.update_sequence_progress()

    def clear_sequence(self):

        while self.sequence_list_layout.count():

            item = self.sequence_list_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

        self.sequence_rows.clear()

    def reset_sequence(self):

        self.completed_steps = 0

        for row_data in self.sequence_rows.values():

            status_label = row_data["status"]

            status_label.setText("WAITING")
            self.apply_status_style(
                status_label,
                "WAITING"
            )
            status_label.setObjectName("sequenceWaiting")
            status_label.style().unpolish(status_label)
            status_label.style().polish(status_label)

        self.update_sequence_progress()

    def update_step_status(self, step_id, status):

        if step_id not in self.sequence_rows:
            return

        row_data = self.sequence_rows[step_id]
        status_label = row_data["status"]

        status = status.upper()

        status_styles = {
            "WAITING": "sequenceWaiting",
            "RUNNING": "sequenceRunning",
            "PASSED": "sequencePassed",
            "FAILED": "sequenceFailed",
            "SKIPPED": "sequenceSkipped",
        }

        status_label.setText(status)
        self.apply_status_style(
            status_label,
            status
        )
        status_label.setObjectName(
            status_styles.get(status, "sequenceWaiting")
        )

        status_label.style().unpolish(status_label)
        status_label.style().polish(status_label)

        self.completed_steps = sum(
            1
            for data in self.sequence_rows.values()
            if data["status"].text() in (
                "PASSED",
                "FAILED",
                "SKIPPED",
            )
        )

        self.update_sequence_progress()

    def update_sequence_progress(self):

        total = self.total_steps

        self.sequence_progress_label.setText(
            f"{self.completed_steps} / {total} Steps"
        )

        percentage = (
            int(self.completed_steps / total * 100)
            if total else 0
        )

        self.sequence_progress.setValue(percentage)

    def apply_status_style(self, label, status):

        colors = {
            "WAITING": "#888888",
            "RUNNING": "#2196F3",
            "PASSED": "#2E9D50",
            "FAILED": "#E53935",
            "SKIPPED": "#AAAAAA",
        }

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.get(status, "#888888")};
                font-weight: bold;
            }}
            """
        )
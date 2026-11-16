
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
)
from PySide6.QtGui import QShortcut, QKeySequence


class TesterWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_ui()

    def setup_ui(self):
        group = QGroupBox("Tester Controls")
        layout = QVBoxLayout(group)

        grid = QGridLayout()

        # Insulation Test Panel
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

        # Withstanding Test Panel
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

        layout.addLayout(grid, 1)

        # Start Test Button
        buttons = QHBoxLayout()

        self.start_button = QPushButton("▶   START TEST")
        self.start_button.setObjectName("startButton")
        self.start_button.setMinimumHeight(85)
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

        # Numpad Enter
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
        layout.addLayout(buttons)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(group)

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
        layout.setContentsMargins(20, 25, 20, 20)

        value_labels = {}

        for name, unit in measurements:
            label = QLabel(f"-- {unit}")
            label.setObjectName("digitalValue")
            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            label.setMinimumHeight(60)

            layout.addRow(f"{name}:", label)

            value_labels[name] = label

        group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        return group, value_labels

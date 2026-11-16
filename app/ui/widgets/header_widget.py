from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
)


class HeaderWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_ui()

    def setup_ui(self):
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

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(header)
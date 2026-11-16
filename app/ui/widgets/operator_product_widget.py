
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QGroupBox,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSizePolicy,
)


class OperatorProductWidget(QWidget):

    # Signals untuk meneruskan event ke MainWindow
    operator_submitted = Signal()
    logout_requested = Signal()
    model_changed = Signal()
    history_tag_submitted = Signal()
    door_top_submitted = Signal()
    door_bottom_submitted = Signal()

    def __init__(self, product_config_db, parent=None):
        super().__init__(parent)

        self.product_config_db = product_config_db

        self.setup_ui()
        self.connect_internal_signals()

    def setup_ui(self):
        group = QGroupBox("Operator & Product Information")
        layout = QHBoxLayout(group)
        layout.setSpacing(15)

        # ==============================================
        # OPERATOR SECTION
        # ==============================================

        operator_group = QGroupBox("Operator")
        operator_form = QFormLayout(operator_group)

        self.operatorid_input = QLineEdit()
        self.operatorname_input = QLineEdit()

        self.operatorid_input.setPlaceholderText(
            "Scan Operator ID and press Enter"
        )

        self.operatorname_input.setReadOnly(True)
        self.operatorname_input.setPlaceholderText("Operator Name")

        self.logout_button = QPushButton("Logout")
        self.logout_button.setEnabled(False)

        operator_form.addRow("Operator ID:", self.operatorid_input)
        operator_form.addRow("Name:", self.operatorname_input)
        operator_form.addRow(self.logout_button)

        # ==============================================
        # PRODUCT SECTION
        # ==============================================

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

        # ==============================================
        # LAYOUT CONFIGURATION
        # ==============================================

        operator_group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        product_group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        layout.addWidget(operator_group, 1)
        layout.addWidget(product_group, 2)

        group.setMaximumHeight(330)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(group)

    def connect_internal_signals(self):

        self.operatorid_input.returnPressed.connect(
            self.operator_submitted.emit
        )

        self.logout_button.clicked.connect(
            self.logout_requested.emit
        )

        self.model_input.currentIndexChanged.connect(
            lambda _index: self.model_changed.emit()
        )

        self.historytag_input.returnPressed.connect(
            self.history_tag_submitted.emit
        )

        self.doortop_input.returnPressed.connect(
            self.door_top_submitted.emit
        )

        self.doorbot_input.returnPressed.connect(
            self.door_bottom_submitted.emit
        )

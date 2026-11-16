
import sys

from PySide6.QtWidgets import QApplication

from app.config import APP_TITLE
from app.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    window = MainWindow()
    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

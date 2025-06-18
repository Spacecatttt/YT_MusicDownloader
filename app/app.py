import logging
import sys

from MainWindow import MainWindow
from PySide6.QtWidgets import (
    QApplication,
)

LOG_FILE = "download_errors.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

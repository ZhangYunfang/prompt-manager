import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from config import Config
from storage.data_store import DataStore
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PromptManager")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    config = Config()
    data_store = DataStore(config.data_dir)

    window = MainWindow(config, data_store)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

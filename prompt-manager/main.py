import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from config import Config
from storage.data_store import DataStore
from ui import theme
from ui.main_window import MainWindow


def _get_icon_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "icon-rounded.ico")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon-rounded.ico")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PromptManager")

    config = Config()
    theme.apply(app, config.appearance, config.accent)

    icon_path = _get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    data_store = DataStore(config.data_dir)

    window = MainWindow(config, data_store)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QInputDialog, QAction, QWidget,
)
from PySide6.QtCore import Qt

from config import Config
from storage.data_store import DataStore
from storage.models import HistoryEntry, BookmarkEntry
from .editor_panel import EditorPanel
from .history_panel import HistoryPanel
from .bookmark_panel import BookmarkPanel
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, config: Config, data_store: DataStore):
        super().__init__()
        self._config = config
        self._data_store = data_store
        self.setWindowTitle("提示词编辑管理")
        self.resize(1100, 650)
        self._build_ui()
        self._build_menu()
        self._load_data()

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        self._history_panel = HistoryPanel()
        self._editor_panel = EditorPanel(self._get_config)
        self._bookmark_panel = BookmarkPanel()

        splitter.addWidget(self._history_panel)
        splitter.addWidget(self._editor_panel)
        splitter.addWidget(self._bookmark_panel)

        splitter.setSizes([220, 600, 220])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        self.setCentralWidget(splitter)

        self._history_panel.entry_selected.connect(self._on_history_selected)
        self._editor_panel.history_saved.connect(self._on_history_saved)
        self._editor_panel.bookmark_requested.connect(self._on_add_bookmark)
        self._bookmark_panel.entry_selected.connect(self._on_bookmark_selected)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _get_config(self) -> Config:
        return self._config

    def _load_data(self):
        self._history_panel.set_entries(self._data_store.get_history())
        self._bookmark_panel.set_entries(self._data_store.get_bookmarks())

    def _on_history_saved(self, entry: HistoryEntry):
        self._data_store.add_history(entry)
        self._history_panel.add_entry(entry)

    def _on_history_selected(self, entry: HistoryEntry):
        self._editor_panel.set_content(entry.content)

    def _on_add_bookmark(self, content: str):
        tags_str, ok = QInputDialog.getText(
            self, "添加收藏", "输入标签（用逗号分隔，可选）:"
        )
        if not ok:
            return
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str.strip() else []

        entry = BookmarkEntry.new(
            content=content,
            source_history_id="",
            tags=tags,
        )
        self._data_store.add_bookmark(entry)
        self._bookmark_panel.add_entry(entry)

    def _on_bookmark_selected(self, entry: BookmarkEntry):
        self._editor_panel.set_content(entry.content)

    def _on_history_deleted(self, entry_id: str):
        self._data_store.delete_history(entry_id)

    def _on_bookmark_deleted(self, entry_id: str):
        self._data_store.delete_bookmark(entry_id)

    def _open_settings(self):
        dialog = SettingsDialog(self._config, self)
        dialog.exec_()

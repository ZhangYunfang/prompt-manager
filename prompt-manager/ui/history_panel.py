from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QMenu, QMessageBox,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt

from storage.models import HistoryEntry


class HistoryPanel(QWidget):
    entry_selected = Signal(HistoryEntry)
    entry_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[HistoryEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("历史记录")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def add_entry(self, entry: HistoryEntry):
        self._all_entries.insert(0, entry)
        self._prepend_item(entry)

    def set_entries(self, entries: list[HistoryEntry]):
        self._all_entries = list(entries)
        self._rebuild_list(entries)

    def _prepend_item(self, entry: HistoryEntry):
        preview = self._format_preview(entry)
        item = QListWidgetItem(preview)
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(entry.content[:500])
        self._list.insertItem(0, item)

    def _rebuild_list(self, entries: list[HistoryEntry]):
        self._list.clear()
        for entry in entries:
            preview = self._format_preview(entry)
            item = QListWidgetItem(preview)
            item.setData(Qt.UserRole, entry.id)
            item.setToolTip(entry.content[:500])
            self._list.addItem(item)

    def _format_preview(self, entry: HistoryEntry) -> str:
        dt = entry.created_at[:16].replace("T", " ")
        line = entry.content.split("\n")[0][:60]
        return f"{dt}  {line}"

    def _on_search(self, keyword: str):
        if not keyword.strip():
            self._rebuild_list(self._all_entries)
            return
        kw = keyword.lower()
        filtered = [e for e in self._all_entries if kw in e.content.lower()]
        self._rebuild_list(filtered)

    def _on_item_clicked(self, item: QListWidgetItem):
        entry_id = item.data(Qt.UserRole)
        for entry in self._all_entries:
            if entry.id == entry_id:
                self.entry_selected.emit(entry)
                return

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        entry_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_entry(entry_id))
        menu.addAction(delete_action)
        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _delete_entry(self, entry_id: str):
        self._all_entries = [e for e in self._all_entries if e.id != entry_id]
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == entry_id:
                self._list.takeItem(i)
                break
        self.entry_deleted.emit(entry_id)

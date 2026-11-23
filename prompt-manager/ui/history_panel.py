from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QMenu,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, Qt

from . import theme, icons
from storage.models import HistoryEntry


class HistoryPanel(QWidget):
    entry_selected = Signal(HistoryEntry)
    entry_deleted = Signal(str)
    clear_requested = Signal()      # 标题后的刷子：请 MainWindow 确认并清空

    def __init__(self, parent=None):
        super().__init__(parent)
        theme.as_panel(self)
        self._all_entries: list[HistoryEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("历史记录")
        header.setObjectName("eyebrow")
        header_row.addWidget(header)

        # 与「我的提示词」的 + 按钮完全同尺寸同规格：14px 图标、24×24、accent 变体
        self._clear_btn = theme.variant(icons.IconButton("", "brush", "accent", 14), "accent")
        self._clear_btn.setObjectName("plus")
        self._clear_btn.setFixedSize(24, 24)
        self._clear_btn.setAccessibleName("清空历史记录")
        self._clear_btn.setToolTip("清空全部历史记录")
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self.clear_requested.emit)
        header_row.addWidget(self._clear_btn)

        header_row.addStretch()
        self._count = QLabel("0")
        self._count.setObjectName("count")
        header_row.addWidget(self._count)
        layout.addLayout(header_row)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索内容…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.keyPressEvent = self._list_key_press
        layout.addWidget(self._list)

    def add_entry(self, entry: HistoryEntry):
        if entry.id in {e.id for e in self._all_entries}:
            return
        self._all_entries.insert(0, entry)
        self._prepend_item(entry)

    def set_entries(self, entries: list[HistoryEntry]):
        self._all_entries = list(entries)
        self._rebuild_list(entries)

    def update_entry(self, entry_id: str, content: str = "", title: str = ""):
        for i, entry in enumerate(self._all_entries):
            if entry.id == entry_id:
                if content:
                    entry.content = content
                if title:
                    entry.title = title
                self._refresh_item(entry_id, entry)
                break

    def _prepend_item(self, entry: HistoryEntry):
        item = self._make_list_item(entry)
        self._list.insertItem(0, item)
        self._sync_count()

    def _rebuild_list(self, entries: list[HistoryEntry]):
        self._list.clear()
        for entry in entries:
            item = self._make_list_item(entry)
            self._list.addItem(item)
        self._sync_count()

    def _sync_count(self):
        count = self._list.count()
        self._count.setText(str(count))
        self._clear_btn.setEnabled(count > 0)

    def _refresh_item(self, entry_id: str, entry: HistoryEntry):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == entry_id:
                item.setText(self._format_label(entry))
                item.setToolTip(entry.content[:500])
                break

    def _make_list_item(self, entry: HistoryEntry) -> QListWidgetItem:
        item = QListWidgetItem(self._format_label(entry))
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(entry.content[:500])
        return item

    def _format_label(self, entry: HistoryEntry) -> str:
        heading = entry.title or entry.content.split("\n")[0][:30]
        dt = entry.updated_at or entry.created_at
        dt = dt[:16].replace("T", " ")
        return f"{heading}\n{dt}"

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
        delete_action.triggered.connect(lambda checked=False, eid=entry_id: self._delete_entry(eid))
        menu.addAction(delete_action)
        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _list_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            item = self._list.currentItem()
            if item:
                entry_id = item.data(Qt.UserRole)
                self._delete_entry(entry_id)
        else:
            QListWidget.keyPressEvent(self._list, event)

    def _delete_entry(self, entry_id: str):
        self._all_entries = [e for e in self._all_entries if e.id != entry_id]
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == entry_id:
                self._list.takeItem(i)
                break
        self._sync_count()
        self.entry_deleted.emit(entry_id)

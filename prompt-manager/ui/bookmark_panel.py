from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QHBoxLayout,
    QApplication,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt

from storage.models import BookmarkEntry


class BookmarkPanel(QWidget):
    entry_selected = Signal(BookmarkEntry)
    entry_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[BookmarkEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("收藏夹")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list.keyPressEvent = self._list_key_press
        layout.addWidget(self._list)

    def set_entries(self, entries: list[BookmarkEntry]):
        self._all_entries = list(entries)
        self._rebuild_list(entries)

    def add_entry(self, entry: BookmarkEntry):
        self._all_entries.insert(0, entry)
        self._prepend_item(entry)

    def _prepend_item(self, entry: BookmarkEntry):
        item = self._make_item(entry)
        self._list.insertItem(0, item)

    def _rebuild_list(self, entries: list[BookmarkEntry]):
        self._list.clear()
        for entry in entries:
            item = self._make_item(entry)
            self._list.addItem(item)

    def _make_item(self, entry: BookmarkEntry) -> QListWidgetItem:
        tags = "  ".join(f"[{t}]" for t in entry.tags) if entry.tags else ""
        heading = entry.title or entry.content.split("\n")[0][:30]
        text = f"{tags}\n{heading}" if tags else heading

        item = QListWidgetItem()
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(entry.content[:500])

        widget = QWidget()
        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(4)

        label = QLabel(text)
        label.setWordWrap(False)
        h.addWidget(label, 1)

        copy_btn = QPushButton("复制")
        copy_btn.setFixedSize(50, 24)
        copy_btn.setStyleSheet("font-size: 11px; padding: 0;")
        copy_btn.clicked.connect(lambda checked=False, e=entry: self._copy_entry(e))
        h.addWidget(copy_btn)

        widget.setMinimumHeight(30)
        item.setSizeHint(widget.sizeHint())
        self._list.setItemWidget(item, widget)
        return item

    def _copy_entry(self, entry: BookmarkEntry):
        QApplication.clipboard().setText(entry.content)

    def _on_item_double_clicked(self, item: QListWidgetItem):
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
        delete_action = QAction("取消收藏", self)
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
        self.entry_deleted.emit(entry_id)

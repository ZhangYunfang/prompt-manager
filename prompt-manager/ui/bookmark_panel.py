from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QMenu, QApplication,
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
        self._list.setStyleSheet("""
            QListWidget {
                background: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                color: #111;
                padding: 5px 8px;
                border-bottom: 1px solid #eee;
                background: transparent;
            }
            QListWidget::item:selected {
                background: #d0e4f7;
                color: #111;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
        """)
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
        heading = entry.title or entry.content.split("\n")[0][:30]
        tags = "  ".join(f"[{t}]" for t in entry.tags) if entry.tags else ""
        display = f"{heading}\n{tags}" if tags else heading

        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(f"双击加载到编辑器\n右键复制或取消收藏\n\n{entry.content[:300]}")
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

        copy_action = QAction("复制内容", self)
        copy_action.triggered.connect(lambda checked=False, eid=entry_id: self._do_copy(eid))
        menu.addAction(copy_action)

        menu.addSeparator()

        delete_action = QAction("取消收藏", self)
        delete_action.triggered.connect(lambda checked=False, eid=entry_id: self._delete_entry(eid))
        menu.addAction(delete_action)

        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _do_copy(self, entry_id: str):
        for entry in self._all_entries:
            if entry.id == entry_id:
                QApplication.clipboard().setText(entry.content)
                break

    def _list_key_press(self, event):
        if event.key() == Qt.Key_Delete:
            item = self._list.currentItem()
            if item:
                self._delete_entry(item.data(Qt.UserRole))
        elif event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            item = self._list.currentItem()
            if item:
                self._do_copy(item.data(Qt.UserRole))
        else:
            QListWidget.keyPressEvent(self._list, event)

    def _delete_entry(self, entry_id: str):
        self._all_entries = [e for e in self._all_entries if e.id != entry_id]
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == entry_id:
                self._list.takeItem(i)
                break
        self.entry_deleted.emit(entry_id)

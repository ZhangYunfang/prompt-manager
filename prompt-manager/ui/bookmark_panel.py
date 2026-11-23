from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QMenu, QApplication, QPushButton,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, Qt

from . import theme, icons
from storage.models import BookmarkEntry


class BookmarkPanel(QWidget):
    entry_selected = Signal(BookmarkEntry)
    entry_deleted = Signal(str)
    new_requested = Signal()      # 标题旁的「+」：新增一条我的提示词

    def __init__(self, parent=None):
        super().__init__(parent)
        theme.as_panel(self)
        self._all_entries: list[BookmarkEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("我的提示词")
        header.setObjectName("eyebrow")
        header_row.addWidget(header)

        self._add_btn = theme.variant(icons.IconButton("", "plus", "accent", 14), "accent")
        self._add_btn.setObjectName("plus")
        self._add_btn.setFixedSize(24, 24)
        self._add_btn.setToolTip("新增：清空输入框，写一条新提示词")
        self._add_btn.setAccessibleName("新增提示词")
        self._add_btn.clicked.connect(self.new_requested.emit)
        header_row.addWidget(self._add_btn)

        header_row.addStretch()
        self._count = QLabel("0")
        self._count.setObjectName("count")
        header_row.addWidget(self._count)
        layout.addLayout(header_row)

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
        self._sync_count()

    def _rebuild_list(self, entries: list[BookmarkEntry]):
        self._list.clear()
        for entry in entries:
            item = self._make_item(entry)
            self._list.addItem(item)
        self._sync_count()

    def _sync_count(self):
        self._count.setText(str(self._list.count()))

    def _make_item(self, entry: BookmarkEntry) -> QListWidgetItem:
        heading = entry.title or entry.content.split("\n")[0][:30]
        tags = "  ".join(f"[{t}]" for t in entry.tags) if entry.tags else ""
        display = f"{heading}\n{tags}" if tags else heading

        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(f"双击加载到编辑器\n右键复制或删除\n\n{entry.content[:300]}")
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

        delete_action = QAction("从我的提示词移除", self)
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
        self._sync_count()
        self.entry_deleted.emit(entry_id)

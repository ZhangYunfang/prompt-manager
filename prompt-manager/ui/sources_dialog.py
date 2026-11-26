from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from . import theme


class SourcesDialog(QDialog):
    """参考来源：列出标题与来源站点，双击行或点「打开原文」用系统浏览器打开。"""

    def __init__(self, sources, parent=None):
        super().__init__(parent)
        self._sources = list(sources or [])
        self.setWindowTitle(f"参考来源（{len(self._sources)}）")
        self.setMinimumSize(620, 420)
        self._build_ui()
        self._fill_rows()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        hint = QLabel("双击一行，或用系统浏览器打开选中的来源")
        hint.setObjectName("dim")
        layout.addWidget(hint)

        self._table = QTableWidget(0, 2, self)
        self._table.setHorizontalHeaderLabels(["标题", "来源站点"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.doubleClicked.connect(lambda _index: self._open_selected())
        layout.addWidget(self._table, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self._open_btn = theme.variant(QPushButton("打开原文"), "primary")
        self._open_btn.clicked.connect(self._open_selected)
        buttons.addWidget(self._open_btn)

        self._copy_btn = theme.variant(QPushButton("复制链接"), "ghost")
        self._copy_btn.clicked.connect(self._copy_selected)
        buttons.addWidget(self._copy_btn)
        buttons.addStretch()

        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.button(QDialogButtonBox.Close).setText("关闭")
        box.rejected.connect(self.reject)
        buttons.addWidget(box)
        layout.addLayout(buttons)

    def _fill_rows(self):
        self._table.setRowCount(len(self._sources))
        for row, item in enumerate(self._sources):
            title = QTableWidgetItem(item.get("title") or item.get("url", ""))
            title.setToolTip(item.get("url", ""))
            self._table.setItem(row, 0, title)
            site = QTableWidgetItem(item.get("site") or "")
            site.setToolTip(item.get("url", ""))
            self._table.setItem(row, 1, site)
        if self._sources:
            self._table.selectRow(0)
        else:
            self._open_btn.setEnabled(False)
            self._copy_btn.setEnabled(False)

    def _current_url(self) -> str:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._sources):
            return ""
        return self._sources[row].get("url", "")

    def _open_selected(self):
        url = self._current_url()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _copy_selected(self):
        url = self._current_url()
        if url:
            QApplication.clipboard().setText(url)

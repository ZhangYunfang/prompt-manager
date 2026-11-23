from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QApplication, QMessageBox, QGridLayout,
)
from PySide6.QtGui import QAction, QPainter, QLinearGradient, QColor
from PySide6.QtCore import Qt, QTimer, Signal, QPoint

from config import Config
from storage.data_store import DataStore
from storage.models import HistoryEntry, BookmarkEntry
from . import theme, icons
from .editor_panel import EditorPanel
from .history_panel import HistoryPanel
from .bookmark_panel import BookmarkPanel
from .bookmark_dialog import BookmarkDialog
from .settings_dialog import SettingsDialog
from .about_dialog import AboutDialog


class _AccentLine(QWidget):
    """顶部流动渐变强调线：底色青→紫，另有一道亮光循环掠过。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._phase = (self._phase + 0.006) % 1.0
        self.update()

    def paintEvent(self, event):
        w = self.width()
        if w <= 0:
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            base = QLinearGradient(0, 0, w, 0)
            base.setColorAt(0.0, QColor(theme.CYAN))
            base.setColorAt(0.5, QColor(theme.PURPLE))
            base.setColorAt(1.0, QColor(theme.CYAN))
            painter.setOpacity(0.55)
            painter.fillRect(self.rect(), base)

            head = self._phase * (w + 240) - 120
            # 黑夜用白光掠过，白天改深墨，否则白底上看不见
            r, g, b = (255, 255, 255) if theme.MODE == "dark" else (22, 32, 47)
            shine = QLinearGradient(head - 120, 0, head + 120, 0)
            shine.setColorAt(0.0, QColor(r, g, b, 0))
            shine.setColorAt(0.5, QColor(r, g, b, 170))
            shine.setColorAt(1.0, QColor(r, g, b, 0))
            painter.setOpacity(1.0)
            painter.fillRect(self.rect(), shine)
        finally:
            painter.end()


class _SwatchPanel(QWidget):
    """弹出的方格色板：4 列铺开，点一个方格即切换主体色并关闭。"""

    picked = Signal(str)
    COLS = 4

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("palette")
        self.setAttribute(Qt.WA_StyledBackground, True)
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(8)
        self._btns = {}
        for i, (key, (label, _a, _b)) in enumerate(theme.ACCENTS.items()):
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(label)
            btn.setAccessibleName(f"主体配色 {label}")
            btn.clicked.connect(lambda _checked=False, k=key: self._choose(k))
            grid.addWidget(btn, i // self.COLS, i % self.COLS)
            self._btns[key] = btn
        self.refresh()

    def refresh(self):
        for k, btn in self._btns.items():
            color = theme.swatch_color(k)
            ring, width = (theme.TEXT, 2) if k == theme.ACCENT else (theme.BORDER, 1)
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: {width}px solid {ring};"
                f" border-radius: 6px; }}"
                f"QPushButton:hover {{ border: 2px solid {theme.TEXT}; }}"
            )

    def _choose(self, key: str):
        self.picked.emit(key)
        self.hide()

    def popup_at(self, anchor):
        """贴在触发按钮下方、右对齐其右缘，且不越出屏幕可用区域。"""
        self.refresh()
        self.adjustSize()
        pos = anchor.mapToGlobal(QPoint(anchor.width() - self.width(), anchor.height() + 8))
        screen = QApplication.screenAt(pos) or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            pos.setX(max(area.left() + 8, min(pos.x(), area.right() - self.width() - 8)))
            pos.setY(min(pos.y(), area.bottom() - self.height() - 8))
        self.move(pos)
        self.show()


class _PaletteButton(icons.IconButton):
    """页头入口：调色板图标，点一下弹出方格色板。"""

    picked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("", "palette", "text", 18, parent)
        self._panel = _SwatchPanel(self)
        self._panel.picked.connect(self.picked.emit)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._open)
        self.set_current(theme.ACCENT)

    def _open(self):
        self._panel.popup_at(self)

    def set_current(self, key: str):
        self._panel.refresh()
        label = theme.ACCENTS.get(key, ("青紫",))[0]
        self.setToolTip(f"主体配色：{label}（点击切换）")
        self.setAccessibleName(f"主体配色 {label}")


class _HeaderBar(QWidget):
    """品牌栏：标题 + 副标 + 右侧模型信息。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self._title = QLabel("提示词管理")
        self._title.setObjectName("brand")
        self._subtitle = QLabel("PROMPT MANAGER")
        self._subtitle.setObjectName("brandSub")
        title_col.addWidget(self._title)
        title_col.addWidget(self._subtitle)
        row.addLayout(title_col)
        row.addStretch()

        self._meta = QLabel("")
        self._meta.setObjectName("dim")
        row.addWidget(self._meta, 0, Qt.AlignBottom)

        self._palette = theme.variant(_PaletteButton(), "outline")
        self._palette.setFixedSize(34, 32)
        row.addWidget(self._palette, 0, Qt.AlignBottom)

        self._appearance_btn = theme.variant(
            icons.IconButton("", "moon", "text", 18), "ghost")
        self._appearance_btn.setFixedSize(34, 32)
        self._appearance_btn.setToolTip("切换黑夜 / 白天外观")
        self._appearance_btn.setCursor(Qt.PointingHandCursor)
        row.addWidget(self._appearance_btn, 0, Qt.AlignBottom)

        layout.addLayout(row)
        layout.addWidget(_AccentLine())

    def set_meta(self, text: str):
        self._meta.setText(text)

    def set_accent(self, key: str):
        self._palette.set_current(key)

    def set_appearance_label(self, mode: str):
        """按钮显示「点一下会切到哪种模式」：现在是黑夜就画月亮（切回白天反之）。"""
        self._appearance_btn.set_kind("moon" if mode == "dark" else "sun")
        self._appearance_btn.setToolTip("切换到白天" if mode == "dark" else "切换到黑夜")


class MainWindow(QMainWindow):
    def __init__(self, config: Config, data_store: DataStore):
        super().__init__()
        self._config = config
        self._data_store = data_store
        self.setWindowTitle("提示词管理")
        self.resize(1160, 740)
        self._build_ui()
        self._build_menu()
        self._load_data()

    def _build_ui(self):
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(14)

        self._header = _HeaderBar()
        self._refresh_meta()
        self._header._appearance_btn.clicked.connect(self._toggle_appearance)
        self._header.set_appearance_label(theme.MODE)
        self._header._palette.picked.connect(self._set_accent)
        self._header.set_accent(theme.ACCENT)
        outer.addWidget(self._header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)

        self._bookmark_panel = BookmarkPanel()
        self._editor_panel = EditorPanel(self._get_config)
        self._history_panel = HistoryPanel()

        # 左：我的提示词 ｜ 中：编辑区 ｜ 右：历史记录
        splitter.addWidget(self._bookmark_panel)
        splitter.addWidget(self._editor_panel)
        splitter.addWidget(self._history_panel)

        splitter.setSizes([260, 620, 260])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setChildrenCollapsible(False)

        outer.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self._history_panel.entry_selected.connect(self._on_history_selected)
        self._history_panel.entry_deleted.connect(self._on_history_deleted)
        self._history_panel.clear_requested.connect(self._on_history_clear_requested)

        self._editor_panel.history_created.connect(self._on_history_created)
        self._editor_panel.history_updated.connect(self._on_history_updated)
        self._editor_panel.bookmark_requested.connect(self._on_bookmark_requested)

        self._bookmark_panel.entry_selected.connect(self._on_bookmark_selected)
        self._bookmark_panel.entry_deleted.connect(self._on_bookmark_deleted)
        # 「我的提示词」标题旁的 + ：新增（清空输入框）
        self._bookmark_panel.new_requested.connect(self._editor_panel.new_prompt)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")

        settings_action = QAction("设置", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("关于")
        about_action = QAction("关于提示词管理", self)
        about_action.triggered.connect(self._open_about)
        help_menu.addAction(about_action)

    def _refresh_meta(self):
        model = self._config.model or "未配置模型"
        key_state = "已连接" if self._config.api_key else "未配置 API Key"
        self._header.set_meta(f"{model}  ·  {key_state}")

    def _toggle_appearance(self):
        self._set_appearance("light" if theme.MODE == "dark" else "dark")

    def _set_accent(self, key: str):
        theme.apply(QApplication.instance(), theme.MODE, key)
        self._config.accent = key
        self._config.save()
        self._header.set_accent(theme.ACCENT)
        icons.recolor_all()
        self._header.update()

    def _set_appearance(self, mode: str):
        theme.apply(QApplication.instance(), mode, theme.ACCENT)
        self._config.appearance = mode
        self._config.save()
        self._header.set_appearance_label(mode)
        self._header.set_accent(theme.ACCENT)
        icons.recolor_all()
        self._header.update()

    def _get_config(self) -> Config:
        return self._config

    def _load_data(self):
        self._history_panel.set_entries(self._data_store.get_history())
        self._bookmark_panel.set_entries(self._data_store.get_bookmarks())

    def _on_history_created(self, entry: HistoryEntry):
        self._data_store.add_history(entry)
        self._history_panel.add_entry(entry)

    def _on_history_updated(self, entry_id: str, content: str, title: str):
        entry = self._data_store.update_history(entry_id, content=content, title=title)
        if entry:
            self._history_panel.update_entry(entry_id, content=content, title=title)

    def _on_history_selected(self, entry: HistoryEntry):
        self._editor_panel.set_content(entry.content)

    def _on_bookmark_requested(self, content: str, cached_title: str, cached_tags: list):
        if cached_title or cached_tags:
            entry = BookmarkEntry.new(
                content=content,
                tags=cached_tags,
                title=cached_title,
            )
        else:
            dialog = BookmarkDialog(self._get_config, content, self)
            if dialog.exec_() != BookmarkDialog.DialogCode.Accepted:
                return
            title, tags = dialog.get_result()
            entry = BookmarkEntry.new(content=content, tags=tags, title=title)
        self._data_store.add_bookmark(entry)
        self._bookmark_panel.add_entry(entry)

    def _on_bookmark_selected(self, entry: BookmarkEntry):
        self._editor_panel.set_content(entry.content)

    def _on_history_clear_requested(self):
        """清空全部历史：不可撤销，必须二次确认。"""
        total = len(self._data_store.get_history())
        if not total:
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("清空历史记录")
        box.setText(f"确定要清空全部 {total} 条历史记录吗？")
        box.setInformativeText("此操作不可撤销。")
        clear_btn = box.addButton("清空", QMessageBox.DestructiveRole)
        box.addButton("取消", QMessageBox.RejectRole)
        box.exec_()
        if box.clickedButton() is not clear_btn:
            return
        self._data_store.clear_history()
        self._history_panel.set_entries([])

    def _on_history_deleted(self, entry_id: str):
        self._data_store.delete_history(entry_id)

    def _on_bookmark_deleted(self, entry_id: str):
        self._data_store.delete_bookmark(entry_id)

    def _open_settings(self):
        dialog = SettingsDialog(self._config, self)
        dialog.exec_()
        self._refresh_meta()

    def _open_about(self):
        dialog = AboutDialog(self)
        dialog.exec_()

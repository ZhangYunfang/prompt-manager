from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QTextBrowser,
    QPushButton, QLabel, QMessageBox, QApplication, QCheckBox, QSplitter,
)
from PySide6.QtCore import Signal, QThread, QTimer, Qt
from PySide6.QtGui import QColor, QPainter

from api.deepseek_client import (
    DeepSeekClient, StreamResult, FORMAT_SYSTEM_PROMPT, OPTIMIZE_SYSTEM_PROMPT,
    markdown_for_display, sources_markdown, strip_outer_fence,
)
from storage.models import HistoryEntry
from . import theme, icons
from .sources_dialog import SourcesDialog


class _StreamWorker(QThread):
    def __init__(self, api_key: str, base_url: str, model: str, action: str, content: str,
                 thinking: bool, search: bool = False):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._action = action
        self._content = content
        self._thinking = thinking
        self._search = search
        self.result = StreamResult()

    def run(self):
        client = DeepSeekClient(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
        )
        system_prompt = FORMAT_SYSTEM_PROMPT if self._action == "format_cleanup" else OPTIMIZE_SYSTEM_PROMPT
        client.stream_call(system_prompt, self._content, self.result,
                           thinking=self._thinking, search=self._search)


class _TitleWorker(QThread):
    done_signal = Signal(str, str)

    def __init__(self, api_key: str, base_url: str, model: str, entry_id: str, content: str):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._entry_id = entry_id
        self._content = content

    def run(self):
        try:
            client = DeepSeekClient(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
            )
            ok, title = client.generate_title(self._content)
            if ok and title:
                self.done_signal.emit(self._entry_id, title.strip()[:12])
            else:
                self.done_signal.emit("", "")
        except Exception:
            self.done_signal.emit("", "")


class _PreFetchWorker(QThread):
    done_signal = Signal(str, object)

    def __init__(self, api_key: str, base_url: str, model: str, content: str):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._content = content

    def run(self):
        try:
            client = DeepSeekClient(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
            )
            ok, data = client.suggest_tags_and_title(self._content)
            if ok and data:
                self.done_signal.emit(data.get("title", ""), data.get("tags", []))
            else:
                self.done_signal.emit("", [])
        except Exception:
            self.done_signal.emit("", [])


class _BlocksLoader(QWidget):
    """6 个方块顺序点亮后清空，AI 调用期间的加载指示。"""

    COUNT = 6
    BLOCK_W = 8
    BLOCK_H = 12
    GAP = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lit = 0
        self.setFixedSize(self.COUNT * self.BLOCK_W + (self.COUNT - 1) * self.GAP, self.BLOCK_H)
        self._timer = QTimer(self)
        self._timer.setInterval(140)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def start(self):
        self._lit = 0
        self.show()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._lit = (self._lit + 1) % (self.COUNT + 1)
        self.update()

    def _colors(self):
        """当前主题强调色，已点亮 235、未点亮 55 透明。"""
        main, _ = theme.accent_pair()
        colors = []
        for i in range(self.COUNT):
            color = QColor(main)
            color.setAlpha(235 if i < self._lit else 55)
            colors.append(color)
        return colors

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        for i, color in enumerate(self._colors()):
            painter.setBrush(color)
            painter.drawRoundedRect(i * (self.BLOCK_W + self.GAP), 0, self.BLOCK_W, self.BLOCK_H, 2, 2)


class EditorPanel(QWidget):
    history_created = Signal(HistoryEntry)
    history_updated = Signal(str, str, str)
    bookmark_requested = Signal(str, str, object)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        # 本控件不再是卡片：上下两半各自是卡片，才能和左右两侧面板的外轮廓一致
        self._config_getter = config_getter
        self._current_history_id = ""
        self._loading = False
        self._stream_worker = None
        self._title_worker = None
        self._prefetch_worker = None
        self._cached_title = ""
        self._cached_tags = []
        self._cached_for_content = ""
        self._last_sources = []
        self._last_result_text = ""
        self._build_ui()

        self._stream_timer = QTimer(self)
        self._stream_timer.setInterval(50)
        self._stream_timer.timeout.connect(self._poll_stream)

        self._prefetch_timer = QTimer(self)
        self._prefetch_timer.setSingleShot(True)
        self._prefetch_timer.setInterval(2000)
        self._prefetch_timer.timeout.connect(self._prefetch)

        self._copy_timer = QTimer(self)
        self._copy_timer.setSingleShot(True)
        self._copy_timer.setInterval(1600)
        self._copy_timer.timeout.connect(self._restore_copy_btn)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 上半：编辑区；下半：AI 结果。各自是一张卡片（跟左右两侧面板同款外轮廓），
        # 中间夹纵向分隔条 —— 这样上下之间的缝看起来就跟左右列之间一样
        top = theme.as_panel(QWidget())
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(16, 14, 16, 14)
        top_layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header = QLabel("编辑区")
        header.setObjectName("eyebrow")
        header_row.addWidget(header)
        header_row.addStretch()

        clear_btn = theme.variant(QPushButton("清除"), "ghost")
        clear_btn.setToolTip("清除内容，下次输入作为新提示词")
        clear_btn.clicked.connect(self._on_clear)
        header_row.addWidget(clear_btn)
        top_layout.addLayout(header_row)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("在这里输入提示词…")
        theme.apply_mono(self._editor, 13)
        self._editor.setTabChangesFocus(True)
        self._editor.textChanged.connect(self._on_text_changed)
        top_layout.addWidget(self._editor, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._thinking_cb = QCheckBox("深度思考")
        self._thinking_cb.setIcon(icons.make("chip", "dim", 14))
        self._thinking_cb.setToolTip("开启后 AI 会更仔细地推理，但耗时更长")
        btn_layout.addWidget(self._thinking_cb)

        self._search_cb = QCheckBox("联网搜索")
        self._search_cb.setToolTip("让 AI 先联网搜索再作答（结果会带参考来源；同时勾选深度思考则是边推理边搜索，更慢）")
        btn_layout.addWidget(self._search_cb)
        btn_layout.addSpacing(4)

        self._format_btn = icons.IconButton("整理格式", "align", "text")
        self._format_btn.setToolTip("修正错字、标点、空格和换行")
        self._format_btn.clicked.connect(lambda: self._run_ai("format_cleanup"))
        btn_layout.addWidget(self._format_btn)

        self._optimize_btn = theme.variant(
            icons.IconButton("优化提示词", "sparkle", "primary"), "primary")
        self._optimize_btn.setToolTip("增强提示词的清晰度和有效性")
        self._optimize_btn.clicked.connect(lambda: self._run_ai("optimize"))
        btn_layout.addWidget(self._optimize_btn)

        self._save_btn = theme.variant(icons.IconButton("保存", "star", "text"), "accent")
        self._save_btn.setToolTip("保存到左侧「我的提示词」")
        self._save_btn.clicked.connect(self._on_bookmark)
        btn_layout.addWidget(self._save_btn)

        btn_layout.addStretch()

        self._new_btn = theme.variant(icons.IconButton("新增", "plus", "text"), "outline")
        self._new_btn.setToolTip("新建一条提示词，清空输入框")
        self._new_btn.clicked.connect(self._on_new_prompt)
        btn_layout.addWidget(self._new_btn)

        top_layout.addLayout(btn_layout)

        bottom = theme.as_panel(QWidget())
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 14, 16, 14)
        bottom_layout.setSpacing(10)

        result_row = QHBoxLayout()
        result_row.setSpacing(8)
        result_header = QLabel("AI 结果")
        result_header.setObjectName("eyebrow")
        result_row.addWidget(result_header)

        self._loader = _BlocksLoader()
        result_row.addWidget(self._loader)
        result_row.addStretch()

        self._sources_btn = theme.variant(QPushButton("参考来源"), "ghost")
        self._sources_btn.setToolTip("查看这次回答用到的网页来源")
        self._sources_btn.setVisible(False)
        self._sources_btn.clicked.connect(self._show_sources)
        result_row.addWidget(self._sources_btn)

        self._copy_btn = theme.variant(icons.IconButton("复制结果", "copy", "text"), "ghost")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_result)
        result_row.addWidget(self._copy_btn)
        bottom_layout.addLayout(result_row)

        self._result_area = QTextBrowser()
        self._result_area.setReadOnly(True)
        self._result_area.setOpenExternalLinks(True)      # 正文里的链接用系统浏览器打开
        self._result_area.setPlaceholderText("整理或优化后的结果将显示在这里…")
        bottom_layout.addWidget(self._result_area, 1)

        self._status = QLabel("字数 0")
        self._status.setObjectName("dim")
        bottom_layout.addWidget(self._status)

        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(theme.SPLITTER_HANDLE)
        self._splitter.addWidget(top)
        self._splitter.addWidget(bottom)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([320, 320])
        layout.addWidget(self._splitter, 1)

    def _on_text_changed(self):
        if self._loading:
            return
        text = self._editor.toPlainText()
        self._set_status(f"字数 {len(text)}")
        if len(text.strip()) > 20:
            self._prefetch_timer.start()

    def _set_status(self, text: str, color: str = ""):
        self._status.setText(text)
        self._status.setStyleSheet(f"color: {color};" if color else "")

    def _prefetch(self):
        content = self._editor.toPlainText().strip()
        if len(content) < 20 or content == self._cached_for_content:
            return
        config = self._config_getter()
        if not config.api_key:
            return
        self._prefetch_worker = _PreFetchWorker(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            content=content,
        )
        self._prefetch_worker.done_signal.connect(self._on_prefetch_ready)
        self._prefetch_worker.start()

    def _on_prefetch_ready(self, title: str, tags: object):
        self._cached_title = title
        self._cached_tags = list(tags) if isinstance(tags, list) else []
        self._cached_for_content = self._editor.toPlainText().strip()

    def _ensure_saved(self):
        content = self._editor.toPlainText().strip()
        if not content:
            return
        if self._current_history_id:
            self.history_updated.emit(self._current_history_id, content, "")
        else:
            entry = HistoryEntry.new(content)
            self._current_history_id = entry.id
            self.history_created.emit(entry)
            self._request_title(entry.id, content)

    def _request_title(self, entry_id: str, content: str):
        config = self._config_getter()
        if not config.api_key:
            return
        self._title_worker = _TitleWorker(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            entry_id=entry_id,
            content=content,
        )
        self._title_worker.done_signal.connect(self._on_title_ready)
        self._title_worker.finished.connect(lambda: setattr(self, '_title_worker', None))
        self._title_worker.start()

    def _on_title_ready(self, entry_id: str, title: str):
        if entry_id and title:
            self.history_updated.emit(entry_id, "", title)

    def _on_clear(self):
        self._editor.clear()
        self._result_area.clear()
        self._last_result_text = ""
        self._copy_btn.setEnabled(False)
        self._copy_timer.stop()          # 别让「已复制」留到下一次结果上
        self._restore_copy_btn()
        self._current_history_id = ""
        self._cached_for_content = ""

    def new_prompt(self):
        """供「我的提示词」面板的 + 按钮调用：清空输入框写新的。"""
        self._on_new_prompt()

    def _on_new_prompt(self):
        self._on_clear()
        self._editor.setFocus()

    def _on_bookmark(self):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "没有内容可以保存")
            return
        self._ensure_saved()

        if content == self._cached_for_content and self._cached_title:
            self.bookmark_requested.emit(content, self._cached_title, self._cached_tags)
        else:
            self.bookmark_requested.emit(content, "", [])

    def _run_ai(self, action: str):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "请先输入提示词内容")
            return

        config = self._config_getter()
        api_key = config.api_key
        if not api_key:
            QMessageBox.warning(self, "提示", "请先在设置中配置 API Key")
            return

        self._ensure_saved()

        self._format_btn.setEnabled(False)
        self._optimize_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._search_cb.setEnabled(False)
        self._sources_btn.setVisible(False)
        self._set_status("正在调用 AI…", theme.CYAN)
        self._loader.start()

        self._stream_worker = _StreamWorker(
            api_key=api_key,
            base_url=config.base_url,
            model=config.model,
            action=action,
            content=content,
            thinking=self._thinking_cb.isChecked(),
            search=self._search_cb.isChecked(),
        )
        self._stream_worker.finished.connect(self._on_stream_done)
        self._stream_timer.start()
        self._stream_worker.start()

    def _poll_stream(self):
        if not self._stream_worker:
            return
        text, done, error = self._stream_worker.result.get()
        if text:
            # 流式期间按纯文本刷（Markdown 半截渲染会跳版），收尾时再统一渲染
            self._result_area.setPlainText(strip_outer_fence(text))
            self._scroll_result_to_end()
        if done:
            self._stream_timer.stop()

    def _scroll_result_to_end(self):
        scrollbar = self._result_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _render_result(self, text, sources=()):
        """剥掉外层围栏 → 末尾补「参考来源」→ 按 Markdown 渲染。"""
        body = strip_outer_fence(text) + sources_markdown(list(sources))
        self._last_result_text = body
        self._result_area.setMarkdown(markdown_for_display(body))
        self._scroll_result_to_end()

    def _on_stream_done(self):
        if not self._stream_worker:
            return
        text, done, error, sources, search_count = self._stream_worker.result.snapshot()
        self._last_sources = sources
        self._stream_timer.stop()
        self._loader.stop()
        # 50ms 轮询可能停在最后一段之前，收尾补一次，否则尾巴会丢
        if text:
            self._render_result(text, sources)
        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)
        self._search_cb.setEnabled(True)

        if sources:
            self._sources_btn.setText(f"参考来源 {len(sources)}")
            self._sources_btn.setVisible(True)
        if not error:
            self._copy_btn.setEnabled(True)
            # 报结果本身的字数：原来报的是左侧编辑区（输入）的字数，容易看成结果不完整
            searched = f" · 搜索 {search_count} 次" if search_count else ""
            self._set_status(f"完成 · 结果 {len(self._last_result_text)} 字{searched}", theme.OK)
        else:
            self._copy_btn.setEnabled(False)
            self._set_status("失败")
            QMessageBox.critical(self, "错误", error)
        self._stream_worker = None

    def _show_sources(self):
        if not self._last_sources:
            return
        SourcesDialog(self._last_sources, self).exec_()

    def _copy_result(self):
        if not self._last_result_text:
            return
        QApplication.clipboard().setText(self._last_result_text)
        # 复制成功的反馈：按钮变「已复制」+ 对勾 + 主题色，1.6s 后自己复原
        self._copy_btn.setText("已复制")
        self._copy_btn.set_kind("check")
        theme.variant(self._copy_btn, "accent")
        self._copy_timer.start()

    def _restore_copy_btn(self):
        self._copy_btn.setText("复制结果")
        self._copy_btn.set_kind("copy")
        theme.variant(self._copy_btn, "ghost")

    def set_content(self, text: str):
        self._loading = True
        self._editor.setPlainText(text)
        self._loading = False

    def get_content(self) -> str:
        return self._editor.toPlainText()

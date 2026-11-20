from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox, QApplication, QCheckBox,
)
from PySide6.QtCore import Signal, QThread, QTimer

from api.deepseek_client import DeepSeekClient, StreamResult, FORMAT_SYSTEM_PROMPT, OPTIMIZE_SYSTEM_PROMPT
from storage.models import HistoryEntry
from . import theme


class _StreamWorker(QThread):
    def __init__(self, api_key: str, base_url: str, model: str, action: str, content: str, thinking: bool):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._action = action
        self._content = content
        self._thinking = thinking
        self.result = StreamResult()

    def run(self):
        client = DeepSeekClient(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
        )
        system_prompt = FORMAT_SYSTEM_PROMPT if self._action == "format_cleanup" else OPTIMIZE_SYSTEM_PROMPT
        client.stream_call(system_prompt, self._content, self.result, thinking=self._thinking)


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


class EditorPanel(QWidget):
    history_created = Signal(HistoryEntry)
    history_updated = Signal(str, str, str)
    bookmark_requested = Signal(str, str, object)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        theme.as_panel(self)
        self._config_getter = config_getter
        self._current_history_id = ""
        self._loading = False
        self._stream_worker = None
        self._title_worker = None
        self._prefetch_worker = None
        self._cached_title = ""
        self._cached_tags = []
        self._cached_for_content = ""
        self._build_ui()

        self._stream_timer = QTimer(self)
        self._stream_timer.setInterval(50)
        self._stream_timer.timeout.connect(self._poll_stream)

        self._prefetch_timer = QTimer(self)
        self._prefetch_timer.setSingleShot(True)
        self._prefetch_timer.setInterval(2000)
        self._prefetch_timer.timeout.connect(self._prefetch)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

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
        layout.addLayout(header_row)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("在这里输入提示词…")
        self._editor.setFont(theme.mono_font(13))
        self._editor.setTabChangesFocus(True)
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor, 3)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._thinking_cb = QCheckBox("深度思考")
        self._thinking_cb.setToolTip("开启后 AI 会更仔细地推理，但耗时更长")
        btn_layout.addWidget(self._thinking_cb)
        btn_layout.addSpacing(4)

        self._format_btn = QPushButton("整理格式")
        self._format_btn.setToolTip("修正错字、标点、空格和换行")
        self._format_btn.clicked.connect(lambda: self._run_ai("format_cleanup"))
        btn_layout.addWidget(self._format_btn)

        self._optimize_btn = theme.variant(QPushButton("优化提示词"), "primary")
        self._optimize_btn.setToolTip("增强提示词的清晰度和有效性")
        self._optimize_btn.clicked.connect(lambda: self._run_ai("optimize"))
        btn_layout.addWidget(self._optimize_btn)

        self._save_btn = theme.variant(QPushButton("保存"), "ghost")
        self._save_btn.clicked.connect(self._manual_save)
        btn_layout.addWidget(self._save_btn)

        btn_layout.addStretch()

        self._bookmark_btn = theme.variant(QPushButton("收藏"), "accent")
        self._bookmark_btn.setToolTip("将当前内容添加到收藏")
        self._bookmark_btn.clicked.connect(self._on_bookmark)
        btn_layout.addWidget(self._bookmark_btn)

        layout.addLayout(btn_layout)

        result_row = QHBoxLayout()
        result_row.setSpacing(8)
        result_header = QLabel("AI 结果")
        result_header.setObjectName("eyebrow")
        result_row.addWidget(result_header)
        result_row.addStretch()

        self._copy_btn = theme.variant(QPushButton("复制结果"), "ghost")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_result)
        result_row.addWidget(self._copy_btn)
        layout.addLayout(result_row)

        self._result_area = QPlainTextEdit()
        self._result_area.setReadOnly(True)
        self._result_area.setPlaceholderText("整理或优化后的结果将显示在这里…")
        self._result_area.setFont(theme.mono_font(13))
        layout.addWidget(self._result_area, 2)

        self._status = QLabel("字数 0")
        self._status.setObjectName("dim")
        layout.addWidget(self._status)

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

    def _manual_save(self):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "没有内容可以保存")
            return
        self._ensure_saved()

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
        self._copy_btn.setEnabled(False)
        self._current_history_id = ""
        self._cached_for_content = ""

    def _on_bookmark(self):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "没有内容可以收藏")
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
        self._set_status("正在调用 AI…", theme.CYAN)

        self._stream_worker = _StreamWorker(
            api_key=api_key,
            base_url=config.base_url,
            model=config.model,
            action=action,
            content=content,
            thinking=self._thinking_cb.isChecked(),
        )
        self._stream_worker.finished.connect(self._on_stream_done)
        self._stream_timer.start()
        self._stream_worker.start()

    def _poll_stream(self):
        if not self._stream_worker:
            return
        text, done, error = self._stream_worker.result.get()
        if text:
            self._result_area.setPlainText(text)
            scrollbar = self._result_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        if done:
            self._stream_timer.stop()

    def _on_stream_done(self):
        if not self._stream_worker:
            return
        text, done, error = self._stream_worker.result.get()
        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)

        if not error:
            self._copy_btn.setEnabled(True)
            self._set_status(f"完成 · 字数 {len(self._editor.toPlainText())}", theme.OK)
        else:
            self._copy_btn.setEnabled(False)
            self._set_status(f"字数 {len(self._editor.toPlainText())}")
            QMessageBox.critical(self, "错误", error)
        self._stream_worker = None

    def _copy_result(self):
        text = self._result_area.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def set_content(self, text: str):
        self._loading = True
        self._editor.setPlainText(text)
        self._loading = False

    def get_content(self) -> str:
        return self._editor.toPlainText()

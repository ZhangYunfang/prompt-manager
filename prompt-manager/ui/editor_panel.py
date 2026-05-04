from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox, QApplication, QCheckBox,
)
from PySide6.QtCore import Signal, QThread, QTimer
from PySide6.QtGui import QFont

from api.deepseek_client import DeepSeekClient
from storage.models import HistoryEntry


class _StreamWorker(QThread):
    chunk_signal = Signal(str)
    done_signal = Signal(bool, str)

    def __init__(self, api_key: str, base_url: str, model: str, action: str, content: str, thinking: bool):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._action = action
        self._content = content
        self._thinking = thinking

    def run(self):
        client = DeepSeekClient(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
        )
        action_map = {
            "format_cleanup": (client.format_cleanup_stream, client.format_cleanup),
            "optimize": (client.optimize_stream, client.optimize),
        }
        stream_fn, fallback_fn = action_map.get(self._action, (None, None))
        if not stream_fn:
            self.done_signal.emit(False, "未知操作")
            return

        content = self._content
        if self._thinking:
            content = "请仔细思考，一步步推理后再给出最终结果：\n" + content

        ok, result = stream_fn(content, self.chunk_signal.emit)
        if not ok or not result:
            ok, result = fallback_fn(content)
            if ok:
                self.chunk_signal.emit(result)
        self.done_signal.emit(ok, "" if ok else result)


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


class _PreFetchWorker(QThread):
    done_signal = Signal(str, object)

    def __init__(self, api_key: str, base_url: str, model: str, content: str):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._content = content

    def run(self):
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


class EditorPanel(QWidget):
    history_created = Signal(HistoryEntry)
    history_updated = Signal(str, str, str)
    bookmark_requested = Signal(str, str, object)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
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

        self._prefetch_timer = QTimer(self)
        self._prefetch_timer.setSingleShot(True)
        self._prefetch_timer.setInterval(2000)
        self._prefetch_timer.timeout.connect(self._prefetch)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        header = QLabel("编辑区")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        header_row.addWidget(header)
        header_row.addStretch()

        clear_btn = QPushButton("清除")
        clear_btn.setFixedWidth(50)
        clear_btn.setToolTip("清除内容，下次输入作为新提示词")
        clear_btn.clicked.connect(self._on_clear)
        header_row.addWidget(clear_btn)
        layout.addLayout(header_row)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("在这里输入提示词...")
        self._editor.setFont(QFont("Consolas", 11))
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor, 2)

        btn_layout = QHBoxLayout()

        self._thinking_cb = QCheckBox("深度思考")
        self._thinking_cb.setToolTip("开启后 AI 会更仔细地推理，但耗时更长")
        btn_layout.addWidget(self._thinking_cb)

        self._format_btn = QPushButton("整理格式")
        self._format_btn.setToolTip("修正错字、标点、空格和换行")
        self._format_btn.clicked.connect(lambda: self._run_ai("format_cleanup"))
        btn_layout.addWidget(self._format_btn)

        self._optimize_btn = QPushButton("优化提示词")
        self._optimize_btn.setToolTip("增强提示词的清晰度和有效性")
        self._optimize_btn.clicked.connect(lambda: self._run_ai("optimize"))
        btn_layout.addWidget(self._optimize_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._manual_save)
        btn_layout.addWidget(self._save_btn)

        btn_layout.addStretch()

        self._bookmark_btn = QPushButton("收藏")
        self._bookmark_btn.setToolTip("将当前内容添加到收藏")
        self._bookmark_btn.clicked.connect(self._on_bookmark)
        btn_layout.addWidget(self._bookmark_btn)

        layout.addLayout(btn_layout)

        result_header = QLabel("AI 结果")
        result_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(result_header)

        self._result_area = QPlainTextEdit()
        self._result_area.setReadOnly(True)
        self._result_area.setPlaceholderText("整理格式或优化后的结果将显示在这里...")
        self._result_area.setFont(QFont("Consolas", 11))
        layout.addWidget(self._result_area, 1)

        result_btn_layout = QHBoxLayout()
        result_btn_layout.addStretch()

        self._copy_btn = QPushButton("复制结果")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_result)
        result_btn_layout.addWidget(self._copy_btn)

        layout.addLayout(result_btn_layout)

        self._status = QLabel("字数: 0")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._status)

    def _on_text_changed(self):
        if self._loading:
            return
        text = self._editor.toPlainText()
        self._status.setText(f"字数: {len(text)}")
        if len(text.strip()) > 20:
            self._prefetch_timer.start()

    def _prefetch(self):
        content = self._editor.toPlainText().strip()
        if len(content) < 20:
            return
        if content == self._cached_for_content:
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
        self._status.setText("正在调用 AI...")

        self._stream_worker = _StreamWorker(
            api_key=api_key,
            base_url=config.base_url,
            model=config.model,
            action=action,
            content=content,
            thinking=self._thinking_cb.isChecked(),
        )
        self._stream_worker.chunk_signal.connect(self._on_stream_chunk)
        self._stream_worker.done_signal.connect(self._on_stream_done)
        self._stream_worker.finished.connect(lambda: setattr(self, '_stream_worker', None))
        self._stream_worker.start()

    def _on_stream_chunk(self, text: str):
        self._result_area.setPlainText(text)
        scrollbar = self._result_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_stream_done(self, ok: bool, error: str):
        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)
        self._status.setText(f"字数: {len(self._editor.toPlainText())}")

        if ok:
            self._copy_btn.setEnabled(True)
        else:
            self._copy_btn.setEnabled(False)
            msg = error or "请求失败，请检查网络或 API 设置"
            QMessageBox.critical(self, "错误", msg)

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

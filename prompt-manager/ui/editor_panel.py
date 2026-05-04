from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox, QApplication,
)
from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QFont

from api.deepseek_client import DeepSeekClient
from storage.models import HistoryEntry


class _StreamWorker(QThread):
    chunk_signal = Signal(str)
    done_signal = Signal(bool, str)

    def __init__(self, api_key: str, base_url: str, model: str, action: str, content: str):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._action = action
        self._content = content

    def run(self):
        client = DeepSeekClient(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
        )
        if self._action == "format_cleanup":
            ok, _ = client.format_cleanup_stream(self._content, self.chunk_signal.emit)
        else:
            ok, _ = client.optimize_stream(self._content, self.chunk_signal.emit)
        self.done_signal.emit(ok, "")


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


class EditorPanel(QWidget):
    history_created = Signal(HistoryEntry)
    history_updated = Signal(str, str, str)
    bookmark_requested = Signal(str)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        self._config_getter = config_getter
        self._current_history_id = ""
        self._loading = False
        self._stream_worker = None
        self._title_worker = None
        self._build_ui()

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

        self._format_btn = QPushButton("整理格式")
        self._format_btn.setToolTip("修正错字、标点、空格和换行")
        self._format_btn.clicked.connect(lambda: self._run_ai("format_cleanup"))
        btn_layout.addWidget(self._format_btn)

        self._optimize_btn = QPushButton("优化提示词")
        self._optimize_btn.setToolTip("增强提示词的清晰度和有效性")
        self._optimize_btn.clicked.connect(lambda: self._run_ai("optimize"))
        btn_layout.addWidget(self._optimize_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setToolTip("保存当前内容到历史记录")
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

    def _on_bookmark(self):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "没有内容可以收藏")
            return
        self._ensure_saved()
        self.bookmark_requested.emit(content)

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
        )
        self._stream_worker.chunk_signal.connect(self._on_stream_chunk)
        self._stream_worker.done_signal.connect(self._on_stream_done)
        self._stream_worker.finished.connect(lambda: setattr(self, '_stream_worker', None))
        self._stream_worker.start()

    def _on_stream_chunk(self, text: str):
        self._result_area.setPlainText(text)

    def _on_stream_done(self, ok: bool, _: str):
        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)
        self._status.setText(f"字数: {len(self._editor.toPlainText())}")

        if ok:
            self._copy_btn.setEnabled(True)
        else:
            self._copy_btn.setEnabled(False)
            QMessageBox.critical(self, "错误", "请求失败，请检查网络或 API 设置")

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

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox, QApplication,
)
from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QFont

from api.deepseek_client import DeepSeekClient
from storage.models import HistoryEntry


class _AIWorker(QThread):
    result_signal = Signal(bool, str)

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
            ok, result = client.format_cleanup(self._content)
        else:
            ok, result = client.optimize(self._content)
        self.result_signal.emit(ok, result)


class EditorPanel(QWidget):
    history_saved = Signal(HistoryEntry)
    bookmark_requested = Signal(str)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        self._config_getter = config_getter
        self._modified = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QLabel("编辑区")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

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
        text = self._editor.toPlainText()
        self._status.setText(f"字数: {len(text)}")
        self._modified = True

    def _on_bookmark(self):
        content = self._editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "提示", "没有内容可以收藏")
            return
        entry = HistoryEntry.new(content)
        self.history_saved.emit(entry)
        self._modified = False
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

        self._format_btn.setEnabled(False)
        self._optimize_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._status.setText("正在调用 AI...")

        self._worker = _AIWorker(
            api_key=api_key,
            base_url=config.base_url,
            model=config.model,
            action=action,
            content=content,
        )
        self._worker.result_signal.connect(self._on_ai_result)
        self._worker.start()

    def _on_ai_result(self, ok: bool, result: str):
        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)
        self._status.setText(f"字数: {len(self._editor.toPlainText())}")

        if ok:
            self._result_area.setPlainText(result)
            self._copy_btn.setEnabled(True)
        else:
            QMessageBox.critical(self, "错误", result)

    def _copy_result(self):
        text = self._result_area.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def set_content(self, text: str):
        self._editor.setPlainText(text)
        self._modified = True

    def get_content(self) -> str:
        return self._editor.toPlainText()

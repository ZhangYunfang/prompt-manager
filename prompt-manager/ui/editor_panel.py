from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from api.deepseek_client import DeepSeekClient
from storage.models import HistoryEntry


class EditorPanel(QWidget):
    history_saved = Signal(HistoryEntry)
    bookmark_requested = Signal(str)

    def __init__(self, config_getter, parent=None):
        super().__init__(parent)
        self._config_getter = config_getter
        self._current_history_id: str = ""
        self._modified = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("编辑区")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("在这里输入提示词...")
        self._editor.setFont(QFont("Consolas", 11))
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        btn_layout = QHBoxLayout()

        self._format_btn = QPushButton("整理格式")
        self._format_btn.setToolTip("修正错字、标点、空格和换行")
        self._format_btn.clicked.connect(self._on_format)
        btn_layout.addWidget(self._format_btn)

        self._optimize_btn = QPushButton("优化提示词")
        self._optimize_btn.setToolTip("增强提示词的清晰度和有效性")
        self._optimize_btn.clicked.connect(self._on_optimize)
        btn_layout.addWidget(self._optimize_btn)

        btn_layout.addStretch()

        self._bookmark_btn = QPushButton("收藏")
        self._bookmark_btn.setToolTip("将当前内容添加到收藏")
        self._bookmark_btn.clicked.connect(self._on_bookmark)
        btn_layout.addWidget(self._bookmark_btn)

        layout.addLayout(btn_layout)

        self._status = QLabel("字数: 0")
        self._status.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._status)

    def _on_text_changed(self):
        text = self._editor.toPlainText()
        self._status.setText(f"字数: {len(text)}")
        self._modified = True

    def _auto_save(self):
        if not self._modified:
            return
        content = self._editor.toPlainText()
        if not content.strip():
            return
        entry = HistoryEntry.new(content)
        self._current_history_id = entry.id
        self.history_saved.emit(entry)
        self._modified = False

    def _on_format(self):
        self._auto_save()
        self._run_ai("format_cleanup")

    def _on_optimize(self):
        self._auto_save()
        self._run_ai("optimize")

    def _on_bookmark(self):
        content = self._editor.toPlainText().strip()
        if not content:
            return
        self._auto_save()
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
        self._status.setText("正在调用 AI...")

        client = DeepSeekClient(
            api_key=api_key,
            base_url=config.base_url,
            model=config.model,
        )

        if action == "format_cleanup":
            ok, result = client.format_cleanup(content)
        else:
            ok, result = client.optimize(content)

        self._format_btn.setEnabled(True)
        self._optimize_btn.setEnabled(True)
        self._status.setText(f"字数: {len(self._editor.toPlainText())}")

        if ok:
            self._editor.setPlainText(result)
            self._modified = True
        else:
            QMessageBox.critical(self, "错误", result)

    def set_content(self, text: str):
        self._editor.setPlainText(text)
        self._modified = True

    def get_content(self) -> str:
        return self._editor.toPlainText()

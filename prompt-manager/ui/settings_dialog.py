from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QVBoxLayout, QLabel, QHBoxLayout,
)
from PySide6.QtCore import Qt, QThread, Signal

from config import Config
from api.deepseek_client import DeepSeekClient
from . import theme


class _TestWorker(QThread):
    result_signal = Signal(bool, str)

    def __init__(self, api_key: str, base_url: str, model: str):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def run(self):
        client = DeepSeekClient(
            api_key=self._api_key,
            base_url=self._base_url,
            model=self._model,
        )
        ok, msg = client.test_connection()
        self.result_signal.emit(ok, msg)


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.Password)
        self._api_key_edit.setPlaceholderText("输入 DeepSeek API Key")

        self._key_toggle_btn = theme.variant(QPushButton("显示"), "ghost")
        self._key_toggle_btn.setFixedWidth(56)
        self._key_toggle_btn.clicked.connect(self._toggle_key_visibility)

        key_row = QHBoxLayout()
        key_row.addWidget(self._api_key_edit)
        key_row.addWidget(self._key_toggle_btn)
        form.addRow("API Key:", key_row)

        self._base_url_edit = QLineEdit()
        form.addRow("API 地址:", self._base_url_edit)

        self._model_edit = QLineEdit()
        form.addRow("模型:", self._model_edit)

        layout.addLayout(form)

        self._test_btn = theme.variant(QPushButton("测试连接"), "accent")
        self._test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self._test_btn)

        self._test_result = QLabel("")
        self._test_result.setWordWrap(True)
        self._test_result.setStyleSheet(f"color: {theme.TEXT_DIM};")
        layout.addWidget(self._test_result)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        theme.variant(buttons.button(QDialogButtonBox.Ok), "primary")
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self):
        self._api_key_edit.setText(self._config.api_key)
        self._base_url_edit.setText(self._config.base_url)
        self._model_edit.setText(self._config.model)

    def _toggle_key_visibility(self):
        if self._api_key_edit.echoMode() == QLineEdit.Password:
            self._api_key_edit.setEchoMode(QLineEdit.Normal)
            self._key_toggle_btn.setText("隐藏")
        else:
            self._api_key_edit.setEchoMode(QLineEdit.Password)
            self._key_toggle_btn.setText("显示")

    def _test_connection(self):
        api_key = self._api_key_edit.text().strip()
        if not api_key:
            self._test_result.setText("请先输入 API Key")
            self._test_result.setStyleSheet(f"color: {theme.WARN};")
            return

        self._test_btn.setEnabled(False)
        self._test_result.setText("正在测试...")
        self._test_result.setStyleSheet(f"color: {theme.TEXT_DIM};")

        self._worker = _TestWorker(
            api_key=api_key,
            base_url=self._base_url_edit.text().strip(),
            model=self._model_edit.text().strip(),
        )
        self._worker.result_signal.connect(self._on_test_result)
        self._worker.start()

    def _on_test_result(self, ok: bool, msg: str):
        self._test_btn.setEnabled(True)
        if ok:
            self._test_result.setText("连接成功")
            self._test_result.setStyleSheet(f"color: {theme.OK};")
        else:
            self._test_result.setText(f"连接失败: {msg}")
            self._test_result.setStyleSheet(f"color: {theme.DANGER};")

    def _save_and_accept(self):
        self._config.api_key = self._api_key_edit.text().strip()
        self._config.base_url = self._base_url_edit.text().strip()
        self._config.model = self._model_edit.text().strip()
        self._config.save()
        self.accept()

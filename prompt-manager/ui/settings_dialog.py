from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QVBoxLayout, QLabel, QMessageBox,
)
from PySide6.QtCore import Qt

from config import Config
from api.deepseek_client import DeepSeekClient


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

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.Password)
        self._api_key_edit.setPlaceholderText("输入 DeepSeek API Key")
        form.addRow("API Key:", self._api_key_edit)

        self._base_url_edit = QLineEdit()
        form.addRow("API 地址:", self._base_url_edit)

        self._model_edit = QLineEdit()
        form.addRow("模型:", self._model_edit)

        layout.addLayout(form)

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)

        self._test_result = QLabel("")
        self._test_result.setStyleSheet("color: gray;")
        layout.addWidget(self._test_result)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self):
        self._api_key_edit.setText(self._config.api_key)
        self._base_url_edit.setText(self._config.base_url)
        self._model_edit.setText(self._config.model)

    def _test_connection(self):
        self._test_result.setText("正在测试...")
        self._test_result.setStyleSheet("color: gray;")
        client = DeepSeekClient(
            api_key=self._api_key_edit.text().strip(),
            base_url=self._base_url_edit.text().strip(),
            model=self._model_edit.text().strip(),
        )
        ok, msg = client.test_connection()
        if ok:
            self._test_result.setText("连接成功")
            self._test_result.setStyleSheet("color: green;")
        else:
            self._test_result.setText(f"连接失败: {msg}")
            self._test_result.setStyleSheet("color: red;")

    def _save_and_accept(self):
        self._config.api_key = self._api_key_edit.text().strip()
        self._config.base_url = self._base_url_edit.text().strip()
        self._config.model = self._model_edit.text().strip()
        self._config.save()
        self.accept()

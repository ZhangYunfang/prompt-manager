from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QDialogButtonBox, QGroupBox,
)
from PySide6.QtCore import QThread, Signal

from api.deepseek_client import DeepSeekClient


class _TagSuggestWorker(QThread):
    done_signal = Signal(bool, str, object)

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
        title = data.get("title", "") if data else ""
        tags = data.get("tags", []) if data else []
        self.done_signal.emit(ok, title, tags)


class BookmarkDialog(QDialog):
    def __init__(self, config_getter, content: str, parent=None):
        super().__init__(parent)
        self._config_getter = config_getter
        self._content = content
        self._tags = []
        self._title = ""
        self._worker = None
        self.setWindowTitle("添加收藏")
        self.setMinimumWidth(400)
        self._build_ui()
        self._load_suggestions()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("标题:"))
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("正在生成...")
        layout.addWidget(self._title_edit)

        layout.addWidget(QLabel("标签:"))
        self._tags_group = QGroupBox("AI 建议标签")
        self._tags_layout = QVBoxLayout(self._tags_group)
        self._status_label = QLabel("正在请求 AI 建议...")
        self._status_label.setStyleSheet("color: gray;")
        self._tags_layout.addWidget(self._status_label)
        layout.addWidget(self._tags_group)

        layout.addWidget(QLabel("自定义标签 (逗号分隔):"))
        self._custom_tags = QLineEdit()
        self._custom_tags.setPlaceholderText("例如: 翻译, 代码, 总结")
        layout.addWidget(self._custom_tags)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_suggestions(self):
        config = self._config_getter()
        if not config.api_key:
            self._status_label.setText("未配置 API Key，请手动输入标签")
            self._status_label.setStyleSheet("color: orange;")
            return

        self._worker = _TagSuggestWorker(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            content=self._content,
        )
        self._worker.done_signal.connect(self._on_suggestions_ready)
        self._worker.start()

    def _on_suggestions_ready(self, ok: bool, title: str, tags: list):
        if ok and title:
            self._title = title
            self._title_edit.setText(title)
            self._checkboxes = []

            self._status_label.hide()
            for tag in tags:
                if isinstance(tag, str):
                    cb = QCheckBox(tag, self._tags_group)
                    cb.setChecked(True)
                    self._checkboxes.append(cb)
                    self._tags_layout.addWidget(cb)
        else:
            self._status_label.setText("AI 建议获取失败，请手动输入")
            self._status_label.setStyleSheet("color: red;")

    def _on_accept(self):
        if self._title_edit.text().strip():
            self._title = self._title_edit.text().strip()

        selected = []
        if hasattr(self, '_checkboxes'):
            for cb in self._checkboxes:
                if cb.isChecked():
                    selected.append(cb.text())

        custom = [t.strip() for t in self._custom_tags.text().split(",") if t.strip()]
        self._tags = selected + custom
        self.accept()

    def get_result(self):
        return self._title, self._tags

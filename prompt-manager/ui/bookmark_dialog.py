from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QDialogButtonBox, QGroupBox,
)
from PySide6.QtCore import QThread, Signal

from api.deepseek_client import DeepSeekClient
from . import theme


class _TagSuggestWorker(QThread):
    done_signal = Signal(bool, str, object)

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
            title = data.get("title", "") if data else ""
            tags = data.get("tags", []) if data else []
        except Exception:
            ok, title, tags = False, "", []
        self.done_signal.emit(ok, title, tags)


class BookmarkDialog(QDialog):
    def __init__(self, config_getter, content: str, parent=None, entry=None):
        """entry 为空＝新增收藏（让 AI 提议标题/标签）；给了 entry＝修改，直接预填、不再请求 AI。"""
        super().__init__(parent)
        self._config_getter = config_getter
        self._content = content
        self._entry = entry
        self._tags = []
        self._title = ""
        self._worker = None
        self._checkboxes = []
        self.setWindowTitle("修改提示词" if entry else "添加收藏")
        self.setMinimumWidth(400)
        self._build_ui()
        if entry:
            self._load_existing()
        else:
            self._load_suggestions()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        layout.addWidget(QLabel("标题:"))
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("正在生成...")
        layout.addWidget(self._title_edit)

        layout.addWidget(QLabel("标签:"))
        self._tags_group = QGroupBox("AI 建议标签")
        self._tags_layout = QVBoxLayout(self._tags_group)
        self._status_label = QLabel("正在请求 AI 建议...")
        self._status_label.setStyleSheet(f"color: {theme.TEXT_DIM};")
        self._tags_layout.addWidget(self._status_label)
        layout.addWidget(self._tags_group)

        layout.addWidget(QLabel("自定义标签 (逗号分隔):"))
        self._custom_tags = QLineEdit()
        self._custom_tags.setPlaceholderText("例如: 翻译, 代码, 总结")
        layout.addWidget(self._custom_tags)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存" if self._entry else "收藏")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        theme.variant(buttons.button(QDialogButtonBox.Ok), "primary")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_existing(self):
        """修改模式：把现有标题与标签填进去，不请求 AI。"""
        self._title_edit.setPlaceholderText("留空则用正文首行")
        self._title_edit.setText(self._entry.title)
        self._title_edit.setFocus()
        self._status_label.hide()
        self._tags_group.setTitle("现有标签")
        for tag in self._entry.tags:
            if isinstance(tag, str) and tag.strip():
                cb = QCheckBox(tag, self._tags_group)
                cb.setChecked(True)
                self._checkboxes.append(cb)
                self._tags_layout.addWidget(cb)
        if not self._checkboxes:
            hint = QLabel("还没有标签，可在下面添加")
            hint.setStyleSheet(f"color: {theme.TEXT_FAINT};")
            self._tags_layout.addWidget(hint)

    def _load_suggestions(self):
        config = self._config_getter()
        if not config.api_key:
            self._status_label.setText("未配置 API Key，请手动输入标签")
            self._status_label.setStyleSheet(f"color: {theme.WARN};")
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
            self._status_label.setStyleSheet(f"color: {theme.DANGER};")

    def _on_accept(self):
        text = self._title_edit.text().strip()
        # 修改模式下允许把标题清空（列表退回显示正文首行）；新增模式空标题就沿用 AI 结果
        if text or self._entry:
            self._title = text

        selected = [cb.text() for cb in self._checkboxes if cb.isChecked()]
        custom = [t.strip() for t in self._custom_tags.text().split(",") if t.strip()]
        tags = []
        for tag in selected + custom:      # 自定义标签可能和已有标签重名，去重保序
            if tag not in tags:
                tags.append(tag)
        self._tags = tags
        self.accept()

    def get_result(self):
        return self._title, self._tags

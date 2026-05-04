# Prompt Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PySide2 desktop app for editing, managing, and bookmarking AI prompts with DeepSeek API integration for format cleanup and prompt optimization.

**Architecture:** Single-window PySide2 app with three resizable panels (history | editor | bookmarks). JSON file storage in `%APPDATA%/prompt-manager/`. DeepSeek API client for two AI actions. Settings dialog for API configuration.

**Tech Stack:** Python 3, PySide2, requests, PyInstaller

**File Structure:**
```
prompt-manager/
├── main.py                 # Entry point
├── config.py               # Settings persistence
├── storage/
│   ├── __init__.py
│   ├── models.py           # Entry dataclasses
│   └── data_store.py       # JSON read/write
├── api/
│   ├── __init__.py
│   └── deepseek_client.py  # API calls
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # Main window + QSplitter
│   ├── editor_panel.py     # Center panel
│   ├── history_panel.py    # Left panel
│   ├── bookmark_panel.py   # Right panel
│   └── settings_dialog.py  # Settings dialog
├── build.spec              # PyInstaller spec
└── requirements.txt
```

---

### Task 1: Project Scaffolding and Dependencies

**Files:**
- Create: `prompt-manager/requirements.txt`
- Create: `prompt-manager/config.py`
- Create: `prompt-manager/storage/__init__.py`
- Create: `prompt-manager/storage/models.py`
- Create: `prompt-manager/api/__init__.py`
- Create: `prompt-manager/ui/__init__.py`

- [ ] **Step 1: Create project directory and requirements.txt**

```bash
mkdir -p prompt-manager/storage prompt-manager/api prompt-manager/ui
```

Write `prompt-manager/requirements.txt`:
```
PySide2>=5.15.0
requests>=2.28.0
pyinstaller>=5.0
```

- [ ] **Step 2: Write storage models**

Write `prompt-manager/storage/models.py`:
```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import uuid


def make_id(prefix: str = "") -> str:
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:4]
    return f"{prefix}{now}-{short}"


@dataclass
class HistoryEntry:
    id: str
    content: str
    created_at: str

    @classmethod
    def new(cls, content: str) -> "HistoryEntry":
        return cls(
            id=make_id(),
            content=content,
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(**d)


@dataclass
class BookmarkEntry:
    id: str
    content: str
    source_history_id: str
    tags: List[str] = field(default_factory=list)
    created_at: str = ""

    @classmethod
    def new(cls, content: str, source_history_id: str, tags: List[str]) -> "BookmarkEntry":
        return cls(
            id=make_id("bkm-"),
            content=content,
            source_history_id=source_history_id,
            tags=tags,
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BookmarkEntry":
        return cls(**d)
```

- [ ] **Step 3: Write config management**

Write `prompt-manager/config.py`:
```python
import json
import os
from pathlib import Path


class Config:
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-v4-flash"

    def __init__(self):
        self._config_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "prompt-manager"
        self._config_file = self._config_dir / "settings.json"
        self._ensure_config_dir()
        self._data = self._load() if self._config_file.exists() else {}
        self._set_defaults()

    def _ensure_config_dir(self):
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _set_defaults(self):
        self._data.setdefault("api_key", "")
        self._data.setdefault("base_url", self.DEFAULT_BASE_URL)
        self._data.setdefault("model", self.DEFAULT_MODEL)

    def _load(self) -> dict:
        with open(self._config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        self._ensure_config_dir()
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def api_key(self) -> str:
        return self._data.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._data["api_key"] = value

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", self.DEFAULT_BASE_URL)

    @base_url.setter
    def base_url(self, value: str):
        self._data["base_url"] = value

    @property
    def model(self) -> str:
        return self._data.get("model", self.DEFAULT_MODEL)

    @model.setter
    def model(self, value: str):
        self._data["model"] = value

    @property
    def data_dir(self) -> Path:
        return self._config_dir
```

- [ ] **Step 4: Write empty __init__.py files**

Write three empty files:
```
prompt-manager/storage/__init__.py
prompt-manager/api/__init__.py
prompt-manager/ui/__init__.py
```

- [ ] **Step 5: Install dependencies**

```bash
cd prompt-manager && pip install -r requirements.txt
```

Expected: PySide2 and requests install successfully.

- [ ] **Step 6: Verify models work**

```bash
cd prompt-manager && python -c "from storage.models import HistoryEntry, BookmarkEntry; h = HistoryEntry.new('test'); print(h.to_dict()); print('OK')"
```

Expected: prints dict and "OK"

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: project scaffolding with models and config"
```

---

### Task 2: JSON Data Store

**Files:**
- Create: `prompt-manager/storage/data_store.py`

- [ ] **Step 1: Write DataStore**

Write `prompt-manager/storage/data_store.py`:
```python
import json
import os
from pathlib import Path
from typing import List

from .models import HistoryEntry, BookmarkEntry


class DataStore:
    def __init__(self, data_dir: Path):
        self._history_file = data_dir / "prompts_history.json"
        self._bookmarks_file = data_dir / "prompts_bookmarks.json"
        self._history: List[HistoryEntry] = []
        self._bookmarks: List[BookmarkEntry] = []
        self._load()

    def _load(self):
        self._history = self._read_entries(self._history_file, HistoryEntry)
        self._bookmarks = self._read_entries(self._bookmarks_file, BookmarkEntry)

    def _read_entries(self, filepath: Path, cls):
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [cls.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def _write_entries(self, filepath: Path, entries: list):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in entries], f, indent=2, ensure_ascii=False)

    # --- History ---

    def get_history(self) -> List[HistoryEntry]:
        return list(self._history)

    def add_history(self, entry: HistoryEntry):
        self._history.insert(0, entry)
        self._write_entries(self._history_file, self._history)

    def delete_history(self, entry_id: str):
        self._history = [e for e in self._history if e.id != entry_id]
        self._write_entries(self._history_file, self._history)

    def search_history(self, keyword: str) -> List[HistoryEntry]:
        kw = keyword.lower()
        return [e for e in self._history if kw in e.content.lower()]

    # --- Bookmarks ---

    def get_bookmarks(self) -> List[BookmarkEntry]:
        return list(self._bookmarks)

    def add_bookmark(self, entry: BookmarkEntry):
        self._bookmarks.insert(0, entry)
        self._write_entries(self._bookmarks_file, self._bookmarks)

    def delete_bookmark(self, entry_id: str):
        self._bookmarks = [e for e in self._bookmarks if e.id != entry_id]
        self._write_entries(self._bookmarks_file, self._bookmarks)
```

- [ ] **Step 2: Test data store**

```bash
cd prompt-manager && python -c "
from storage.data_store import DataStore
from storage.models import HistoryEntry, BookmarkEntry
import tempfile, os

with tempfile.TemporaryDirectory() as d:
    store = DataStore(d)
    h = HistoryEntry.new('hello world')
    store.add_history(h)
    items = store.get_history()
    assert len(items) == 1
    assert items[0].content == 'hello world'
    print('History OK')

    b = BookmarkEntry.new('test prompt', h.id, ['tag1'])
    store.add_bookmark(b)
    bms = store.get_bookmarks()
    assert len(bms) == 1
    assert bms[0].tags == ['tag1']
    print('Bookmarks OK')

    results = store.search_history('hello')
    assert len(results) == 1
    print('Search OK')

    store.delete_history(h.id)
    assert len(store.get_history()) == 0
    print('Delete OK')

print('All tests passed')
"
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: JSON data store for history and bookmarks"
```

---

### Task 3: DeepSeek API Client

**Files:**
- Create: `prompt-manager/api/deepseek_client.py`

- [ ] **Step 1: Write API client**

Write `prompt-manager/api/deepseek_client.py`:
```python
from typing import Optional, Tuple
import requests


FORMAT_SYSTEM_PROMPT = (
    "You are a text formatter. Fix the following prompt text: "
    "correct typos, add missing punctuation and brackets, "
    "remove extra spaces and line breaks. "
    "Output ONLY the corrected text, no explanations."
)

OPTIMIZE_SYSTEM_PROMPT = (
    "You are a prompt engineering expert. Improve the following prompt "
    "to make it clearer, more specific, and more effective. "
    "Output ONLY the improved prompt, no explanations."
)

TIMEOUT = 30


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-v4-flash"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def _call(self, system_prompt: str, user_content: str) -> Tuple[bool, str]:
        if not self._api_key:
            return False, "请先在设置中配置 API Key"

        try:
            resp = requests.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.3,
                },
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            result = data["choices"][0]["message"]["content"]
            return True, result
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络后重试"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 API 服务器，请检查网络和 API 地址"
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                return False, "API Key 无效，请在设置中更新"
            return False, f"API 错误 ({resp.status_code}): {e}"
        except Exception as e:
            return False, f"未知错误: {e}"

    def format_cleanup(self, content: str) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, content)

    def optimize(self, content: str) -> Tuple[bool, str]:
        return self._call(OPTIMIZE_SYSTEM_PROMPT, content)

    def test_connection(self) -> Tuple[bool, str]:
        return self._call(FORMAT_SYSTEM_PROMPT, "test")
```

- [ ] **Step 2: Quick smoke test (no API key)**

```bash
cd prompt-manager && python -c "
from api.deepseek_client import DeepSeekClient
c = DeepSeekClient('')
ok, msg = c.test_connection()
assert not ok
assert 'API Key' in msg
print('No-key test passed:', msg)
"
```

Expected: prints error about missing API key.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: DeepSeek API client for format and optimize"
```

---

### Task 4: Settings Dialog

**Files:**
- Create: `prompt-manager/ui/settings_dialog.py`

- [ ] **Step 1: Write settings dialog**

Write `prompt-manager/ui/settings_dialog.py`:
```python
from PySide2.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QVBoxLayout, QLabel, QMessageBox,
)
from PySide2.QtCore import Qt

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
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: settings dialog for API configuration"
```

---

### Task 5: Editor Panel

**Files:**
- Create: `prompt-manager/ui/editor_panel.py`

- [ ] **Step 1: Write editor panel**

Write `prompt-manager/ui/editor_panel.py`:
```python
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox,
)
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QFont

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
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: editor panel with AI actions and auto-save"
```

---

### Task 6: History Panel

**Files:**
- Create: `prompt-manager/ui/history_panel.py`

- [ ] **Step 1: Write history panel**

Write `prompt-manager/ui/history_panel.py`:
```python
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QMenu, QAction, QMessageBox,
)
from PySide2.QtCore import Signal, Qt

from storage.models import HistoryEntry


class HistoryPanel(QWidget):
    entry_selected = Signal(HistoryEntry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[HistoryEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("历史记录")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

    def add_entry(self, entry: HistoryEntry):
        self._all_entries.insert(0, entry)
        self._prepend_item(entry)

    def set_entries(self, entries: list[HistoryEntry]):
        self._all_entries = list(entries)
        self._rebuild_list(entries)

    def _prepend_item(self, entry: HistoryEntry):
        preview = self._format_preview(entry)
        item = QListWidgetItem(preview)
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(entry.content[:500])
        self._list.insertItem(0, item)

    def _rebuild_list(self, entries: list[HistoryEntry]):
        self._list.clear()
        for entry in entries:
            preview = self._format_preview(entry)
            item = QListWidgetItem(preview)
            item.setData(Qt.UserRole, entry.id)
            item.setToolTip(entry.content[:500])
            self._list.addItem(item)

    def _format_preview(self, entry: HistoryEntry) -> str:
        dt = entry.created_at[:16].replace("T", " ")
        line = entry.content.split("\n")[0][:60]
        return f"{dt}  {line}"

    def _on_search(self, keyword: str):
        if not keyword.strip():
            self._rebuild_list(self._all_entries)
            return
        kw = keyword.lower()
        filtered = [e for e in self._all_entries if kw in e.content.lower()]
        self._rebuild_list(filtered)

    def _on_item_clicked(self, item: QListWidgetItem):
        entry_id = item.data(Qt.UserRole)
        for entry in self._all_entries:
            if entry.id == entry_id:
                self.entry_selected.emit(entry)
                return

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        entry_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_entry(entry_id))
        menu.addAction(delete_action)
        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _delete_entry(self, entry_id: str):
        self._all_entries = [e for e in self._all_entries if e.id != entry_id]
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == entry_id:
                self._list.takeItem(i)
                break
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: history panel with search and context menu"
```

---

### Task 7: Bookmark Panel

**Files:**
- Create: `prompt-manager/ui/bookmark_panel.py`

- [ ] **Step 1: Write bookmark panel**

Write `prompt-manager/ui/bookmark_panel.py`:
```python
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMenu, QAction, QHBoxLayout,
    QApplication, QInputDialog, QMessageBox,
)
from PySide2.QtCore import Signal, Qt

from storage.models import BookmarkEntry


class BookmarkPanel(QWidget):
    entry_selected = Signal(BookmarkEntry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_entries: list[BookmarkEntry] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        header = QLabel("收藏夹")
        header.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(header)

        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)

    def set_entries(self, entries: list[BookmarkEntry]):
        self._all_entries = list(entries)
        self._rebuild_list(entries)

    def add_entry(self, entry: BookmarkEntry):
        self._all_entries.insert(0, entry)
        self._prepend_item(entry)

    def _prepend_item(self, entry: BookmarkEntry):
        item = self._make_item(entry)
        self._list.insertItem(0, item)

    def _rebuild_list(self, entries: list[BookmarkEntry]):
        self._list.clear()
        for entry in entries:
            item = self._make_item(entry)
            self._list.addItem(item)

    def _make_item(self, entry: BookmarkEntry) -> QListWidgetItem:
        tags = "  ".join(f"[{t}]" for t in entry.tags) if entry.tags else ""
        preview = entry.content.split("\n")[0][:40]
        text = f"{tags}  {preview}" if tags else preview
        item = QListWidgetItem()
        item.setData(Qt.UserRole, entry.id)
        item.setToolTip(entry.content[:500])

        widget = QWidget()
        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(4)

        label = QLabel(text)
        label.setWordWrap(False)
        h.addWidget(label, 1)

        copy_btn = QPushButton("复制")
        copy_btn.setFixedSize(50, 24)
        copy_btn.setStyleSheet("font-size: 11px; padding: 0;")
        copy_btn.clicked.connect(lambda checked=None, e=entry: self._copy_entry(e))
        h.addWidget(copy_btn)

        item.setSizeHint(widget.sizeHint())
        self._list.setItemWidget(item, widget)
        return item

    def _copy_entry(self, entry: BookmarkEntry):
        QApplication.clipboard().setText(entry.content)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        entry_id = item.data(Qt.UserRole)
        for entry in self._all_entries:
            if entry.id == entry_id:
                self.entry_selected.emit(entry)
                return

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        entry_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        delete_action = QAction("取消收藏", self)
        delete_action.triggered.connect(lambda: self._delete_entry(entry_id))
        menu.addAction(delete_action)
        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def _delete_entry(self, entry_id: str):
        self._all_entries = [e for e in self._all_entries if e.id != entry_id]
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == entry_id:
                self._list.takeItem(i)
                break
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: bookmark panel with copy and context menu"
```

---

### Task 8: Main Window

**Files:**
- Create: `prompt-manager/ui/main_window.py`

- [ ] **Step 1: Write main window**

Write `prompt-manager/ui/main_window.py`:
```python
from PySide2.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QInputDialog, QAction, QWidget,
)
from PySide2.QtCore import Qt

from config import Config
from storage.data_store import DataStore
from storage.models import HistoryEntry, BookmarkEntry
from .editor_panel import EditorPanel
from .history_panel import HistoryPanel
from .bookmark_panel import BookmarkPanel
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, config: Config, data_store: DataStore):
        super().__init__()
        self._config = config
        self._data_store = data_store
        self.setWindowTitle("提示词编辑管理")
        self.resize(1100, 650)
        self._build_ui()
        self._build_menu()
        self._load_data()

    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        self._history_panel = HistoryPanel()
        self._editor_panel = EditorPanel(self._get_config)
        self._bookmark_panel = BookmarkPanel()

        splitter.addWidget(self._history_panel)
        splitter.addWidget(self._editor_panel)
        splitter.addWidget(self._bookmark_panel)

        splitter.setSizes([220, 600, 220])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        self.setCentralWidget(splitter)

        self._history_panel.entry_selected.connect(self._on_history_selected)
        self._editor_panel.history_saved.connect(self._on_history_saved)
        self._editor_panel.bookmark_requested.connect(self._on_add_bookmark)
        self._bookmark_panel.entry_selected.connect(self._on_bookmark_selected)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _get_config(self) -> Config:
        return self._config

    def _load_data(self):
        self._history_panel.set_entries(self._data_store.get_history())
        self._bookmark_panel.set_entries(self._data_store.get_bookmarks())

    def _on_history_saved(self, entry: HistoryEntry):
        self._data_store.add_history(entry)
        self._history_panel.add_entry(entry)

    def _on_history_selected(self, entry: HistoryEntry):
        self._editor_panel.set_content(entry.content)

    def _on_add_bookmark(self, content: str):
        tags_str, ok = QInputDialog.getText(
            self, "添加收藏", "输入标签（用逗号分隔，可选）:"
        )
        if not ok:
            return
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str.strip() else []

        entry = BookmarkEntry.new(
            content=content,
            source_history_id="",
            tags=tags,
        )
        self._data_store.add_bookmark(entry)
        self._bookmark_panel.add_entry(entry)

    def _on_bookmark_selected(self, entry: BookmarkEntry):
        self._editor_panel.set_content(entry.content)

    def _on_history_deleted(self, entry_id: str):
        self._data_store.delete_history(entry_id)

    def _on_bookmark_deleted(self, entry_id: str):
        self._data_store.delete_bookmark(entry_id)

    def _open_settings(self):
        dialog = SettingsDialog(self._config, self)
        dialog.exec_()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: main window assembling three panels"
```

---

### Task 9: Entry Point

**Files:**
- Create: `prompt-manager/main.py`

- [ ] **Step 1: Write entry point**

Write `prompt-manager/main.py`:
```python
import sys
import os

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QFont

from config import Config
from storage.data_store import DataStore
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PromptManager")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    config = Config()
    data_store = DataStore(config.data_dir)

    window = MainWindow(config, data_store)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the app**

```bash
cd prompt-manager && python main.py
```

Expected: App launches with three-panel layout. Editor accepts text. Settings dialog opens.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: entry point and working desktop app"
```

---

### Task 10: PyInstaller Packaging

**Files:**
- Create: `prompt-manager/build.spec`

- [ ] **Step 1: Write PyInstaller spec**

Write `prompt-manager/build.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide2.QtWebEngine',
        'PySide2.QtWebEngineCore',
        'PySide2.QtWebEngineWidgets',
        'PySide2.QtQml',
        'PySide2.QtQuick',
        'PySide2.QtQuickWidgets',
        'PySide2.QtMultimedia',
        'PySide2.QtMultimediaWidgets',
        'PySide2.QtSensors',
        'PySide2.QtPositioning',
        'PySide2.QtLocation',
        'PySide2.QtWebChannel',
        'PySide2.QtWebSockets',
        'PySide2.QtSql',
        'PySide2.QtTest',
        'PySide2.QtXmlPatterns',
        'PySide2.QtHelp',
        'PySide2.QtUiTools',
        'PySide2.QtDesigner',
        'PySide2.QtScript',
        'PySide2.QtScriptTools',
        'PySide2.QtSvg',
        'PySide2.QtWinExtras',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PromptManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- [ ] **Step 2: Build executable**

```bash
cd prompt-manager && pyinstaller --clean build.spec
```

Expected: Build completes. Executable at `dist/PromptManager/PromptManager.exe`.

- [ ] **Step 3: Verify executable size**

```bash
ls -lh prompt-manager/dist/PromptManager/
```

Expected: Total directory size < 50MB.

- [ ] **Step 4: Test executable**

```bash
./prompt-manager/dist/PromptManager/PromptManager.exe
```

Expected: App launches without console window. All features work.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: PyInstaller packaging spec"
```

---

### Task 11: Polish and Edge Cases

**Files:**
- Modify: `prompt-manager/ui/settings_dialog.py`
- Modify: `prompt-manager/ui/editor_panel.py`
- Modify: `prompt-manager/ui/main_window.py`

- [ ] **Step 1: Wire delete signals from panels to data store**

Add `deleted` signals to `HistoryPanel`:
```python
# In HistoryPanel.__init__, add signal:
entry_deleted = Signal(str)

# In _delete_entry, after removing from list, emit:
self.entry_deleted.emit(entry_id)
```

Add `deleted` signals to `BookmarkPanel`:
```python
# In BookmarkPanel.__init__, add signal:
entry_deleted = Signal(str)

# In _delete_entry, after removing from list, emit:
self.entry_deleted.emit(entry_id)
```

In `MainWindow._build_ui`, connect delete signals:
```python
self._history_panel.entry_deleted.connect(self._on_history_deleted)
self._bookmark_panel.entry_deleted.connect(self._on_bookmark_deleted)
```

- [ ] **Step 2: Add API key show/hide toggle to settings**

Add toggle button next to API key field in SettingsDialog:
```python
# After creating self._api_key_edit, add toggle:
self._toggle_btn = QPushButton("显示")
self._toggle_btn.setFixedWidth(50)
self._toggle_btn.clicked.connect(self._toggle_key_visibility)
# Add to form layout as a row with the key edit

def _toggle_key_visibility(self):
    if self._api_key_edit.echoMode() == QLineEdit.Password:
        self._api_key_edit.setEchoMode(QLineEdit.Normal)
        self._toggle_btn.setText("隐藏")
    else:
        self._api_key_edit.setEchoMode(QLineEdit.Password)
        self._toggle_btn.setText("显示")
```

- [ ] **Step 3: Handle empty editor gracefully**

In `EditorPanel._on_bookmark`, if content is empty:
```python
def _on_bookmark(self):
    content = self._editor.toPlainText().strip()
    if not content:
        QMessageBox.information(self, "提示", "没有内容可以收藏")
        return
    self._auto_save()
    self.bookmark_requested.emit(content)
```

- [ ] **Step 4: Prevent duplicate auto-save for same unmodified content**

In `EditorPanel`:
```python
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
```

- [ ] **Step 5: Run full app and smoke test**

```bash
cd prompt-manager && python main.py
```

Manual test:
1. Type text in editor — verify char count updates
2. Click "整理格式" without API key — verify warning dialog appears
3. Enter settings, set API key, test connection
4. Click "整理格式" — verify loading state and result
5. Click "优化提示词" — verify loading state and result
6. Click "收藏" — verify tag input dialog appears
7. Check history list has entries
8. Click history entry — verify it loads in editor
9. Click bookmark "复制" button — verify clipboard has content
10. Right-click delete on history and bookmark items

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: polish signals, toggle key visibility, edge cases"
```

---

## Verification Checklist

Before considering the project complete:

- [ ] App launches without errors
- [ ] Editor accepts text, char count updates in real-time
- [ ] Auto-save creates history entries on focus loss or AI action
- [ ] History list shows timestamp + preview; click to load
- [ ] History search filters correctly
- [ ] "整理格式" works with valid API key
- [ ] "优化提示词" works with valid API key
- [ ] Both AI buttons show loading state and handle errors gracefully
- [ ] Bookmark with tags works
- [ ] Bookmark "复制" copies to clipboard
- [ ] Right-click delete on history and bookmarks
- [ ] Settings dialog saves and persists API key
- [ ] Test connection button works
- [ ] Executable builds with PyInstaller under 50MB

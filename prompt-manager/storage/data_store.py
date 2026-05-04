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
        except (json.JSONDecodeError, TypeError):
            return []

    def _write_entries(self, filepath: Path, entries: list):
        tmp = filepath.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in entries], f, indent=2, ensure_ascii=False)
            tmp.replace(filepath)
        except OSError as e:
            raise OSError(f"Failed to persist {filepath.name}: {e}") from e

    # --- History ---

    def get_history(self) -> List[HistoryEntry]:
        return list(self._history)

    def add_history(self, entry: HistoryEntry):
        self._history.insert(0, entry)
        self._write_entries(self._history_file, self._history)

    def delete_history(self, entry_id: str):
        self._history = [e for e in self._history if e.id != entry_id]
        self._write_entries(self._history_file, self._history)

    def update_history(self, entry_id: str, content: str = "", title: str = ""):
        for entry in self._history:
            if entry.id == entry_id:
                entry.update(content=content, title=title)
                self._write_entries(self._history_file, self._history)
                return entry
        return None

    def get_history_entry(self, entry_id: str):
        for entry in self._history:
            if entry.id == entry_id:
                return entry
        return None

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

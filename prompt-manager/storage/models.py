from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List
import uuid


def make_id(prefix: str = "") -> str:
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:4]
    return f"{prefix}{now}-{short}"


@dataclass
class HistoryEntry:
    id: str
    content: str
    title: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def new(cls, content: str, title: str = "") -> "HistoryEntry":
        now = datetime.now().isoformat()
        return cls(
            id=make_id(),
            content=content,
            title=title,
            created_at=now,
            updated_at=now,
        )

    def update(self, content: str = "", title: str = ""):
        if content:
            self.content = content
        if title:
            self.title = title
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        d = dict(d)
        d.setdefault("title", "")
        d.setdefault("updated_at", d.get("created_at", ""))
        return cls(**d)


@dataclass
class BookmarkEntry:
    id: str
    content: str
    source_history_id: str = ""
    title: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""

    @classmethod
    def new(cls, content: str, source_history_id: str = "", tags: list = None, title: str = "") -> "BookmarkEntry":
        return cls(
            id=make_id("bkm-"),
            content=content,
            source_history_id=source_history_id,
            title=title,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BookmarkEntry":
        d = dict(d)
        d.setdefault("source_history_id", "")
        d.setdefault("title", "")
        d.setdefault("tags", [])
        d.setdefault("created_at", "")
        return cls(**d)

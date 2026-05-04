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

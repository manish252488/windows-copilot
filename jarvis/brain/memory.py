from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Deque


@dataclass
class Message:
    role: str
    content: str
    timestamp: str


class ConversationMemory:
    def __init__(self, memory_file: Path, max_short_term: int = 12) -> None:
        self.memory_file = memory_file
        self.max_short_term = max_short_term
        self.short_term: Deque[Message] = deque(maxlen=max_short_term)
        self.long_term: dict = {"preferences": {}, "frequent_commands": {}}
        self._load()

    def _load(self) -> None:
        if not self.memory_file.exists():
            return
        payload = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.long_term = payload.get("long_term", self.long_term)
        for item in payload.get("short_term", []):
            self.short_term.append(Message(**item))

    def save(self) -> None:
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "short_term": [asdict(msg) for msg in self.short_term],
            "long_term": self.long_term,
        }
        self.memory_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, role: str, content: str) -> None:
        self.short_term.append(
            Message(role=role, content=content, timestamp=datetime.now(UTC).isoformat())
        )
        if role == "user":
            freq = self.long_term["frequent_commands"]
            freq[content] = freq.get(content, 0) + 1
        self.save()

    def as_chat_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.short_term]

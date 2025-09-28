"""Local state cache for agent context."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AgentState:
    """Persisted agent state for providing continuity between frames."""

    last_frame_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def update(self, frame_id: str, delta: Optional[Dict[str, Any]]) -> None:
        self.last_frame_id = frame_id
        if delta:
            self.context.update(delta)

    def to_json(self) -> str:
        return json.dumps({"last_frame_id": self.last_frame_id, "context": self.context})

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf8"))
        return cls(last_frame_id=data.get("last_frame_id"), context=data.get("context", {}))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf8")


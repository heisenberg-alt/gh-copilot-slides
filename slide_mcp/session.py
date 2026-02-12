"""
Session persistence — saves and loads presentation sessions.

Sessions are stored as JSON files in a `.slide-sessions/` directory,
enabling the edit loop to persist across CLI invocations and MCP tool calls.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field, fields as dataclass_fields
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("slide-builder.session")

SESSIONS_DIR_NAME = ".slide-sessions"

# Session IDs must be lowercase hex only (prevents path traversal)
_SESSION_ID_RE = re.compile(r"^[a-f0-9]{1,32}$")


@dataclass
class PresentationSession:
    """Persistent state for a presentation pipeline run."""

    id: str = ""
    topic: str = ""
    purpose: str = "presentation"
    research_data: dict[str, Any] = field(default_factory=dict)
    slides: list[dict[str, Any]] = field(default_factory=list)
    presentation_title: str = ""
    style_name: str = ""
    custom_preset: dict[str, Any] | None = None
    output_paths: dict[str, str] = field(default_factory=dict)
    edit_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    # Additional context
    urls: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    mood: str = ""
    audience: str = ""
    slide_count: int = 10
    output_formats: list[str] = field(default_factory=lambda: ["html"])

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict."""
        d = {
            "id": self.id,
            "topic": self.topic,
            "purpose": self.purpose,
            "research_data": self.research_data,
            "slides": self.slides,
            "presentation_title": self.presentation_title,
            "style_name": self.style_name,
            "custom_preset": self.custom_preset,
            "output_paths": self.output_paths,
            "edit_history": self.edit_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "urls": self.urls,
            "files": self.files,
            "mood": self.mood,
            "audience": self.audience,
            "slide_count": self.slide_count,
            "output_formats": self.output_formats,
        }
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresentationSession:
        """Deserialize from a dict, only setting known dataclass fields."""
        session = cls()
        allowed = {f.name for f in dataclass_fields(cls)}
        for key, value in data.items():
            if key in allowed:
                setattr(session, key, value)
        return session

    def add_edit(self, instruction: str, summary: str) -> None:
        """Record an edit in the history."""
        self.edit_history.append({
            "instruction": instruction,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        })
        self.updated_at = datetime.now().isoformat()


class SessionManager:
    """Manages session persistence to JSON files."""

    def __init__(self, workspace_dir: str = "."):
        self.sessions_dir = Path(workspace_dir) / SESSIONS_DIR_NAME
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        if not _SESSION_ID_RE.match(session_id):
            raise ValueError(
                f"Invalid session ID '{session_id}': must be 1-32 lowercase hex characters"
            )
        return self.sessions_dir / f"{session_id}.json"

    def create(self, **kwargs: Any) -> PresentationSession:
        """Create and save a new session."""
        session = PresentationSession(**kwargs)
        self.save(session)
        logger.info(f"Created session: {session.id}")
        return session

    def save(self, session: PresentationSession) -> None:
        """Save a session to disk with restrictive file permissions."""
        session.updated_at = datetime.now().isoformat()
        path = self._session_path(session.id)
        path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
        path.chmod(0o600)

    def load(self, session_id: str) -> PresentationSession:
        """Load a session from disk."""
        path = self._session_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        return PresentationSession.from_dict(data)

    def list_sessions(self) -> list[dict[str, str]]:
        """List all sessions with brief info."""
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                sessions.append({
                    "id": data.get("id", path.stem),
                    "topic": data.get("topic", ""),
                    "style": data.get("style_name", ""),
                    "slides": str(len(data.get("slides", []))),
                    "updated": data.get("updated_at", ""),
                })
            except Exception:
                continue
        return sessions

    def latest(self) -> PresentationSession | None:
        """Load the most recently updated session."""
        sessions = self.list_sessions()
        if not sessions:
            return None
        return self.load(sessions[0]["id"])

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

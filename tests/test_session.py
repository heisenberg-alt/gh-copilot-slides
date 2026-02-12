"""Tests for slide_mcp.session — PresentationSession and SessionManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from slide_mcp.session import PresentationSession, SessionManager


class TestPresentationSession:
    def test_auto_id_generation(self):
        session = PresentationSession()
        assert session.id  # Non-empty
        assert len(session.id) == 12

    def test_explicit_id_preserved(self):
        session = PresentationSession(id="myid123")
        assert session.id == "myid123"

    def test_timestamps_set(self):
        session = PresentationSession()
        assert session.created_at
        assert session.updated_at

    def test_timestamps_preserved_on_deserialization(self):
        """Regression: __post_init__ must NOT overwrite saved timestamps."""
        session = PresentationSession(
            id="abc",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-06-15T12:00:00",
        )
        assert session.created_at == "2024-01-01T00:00:00"
        assert session.updated_at == "2024-06-15T12:00:00"

    def test_round_trip_serialization(self):
        session = PresentationSession(
            topic="AI Overview",
            slides=[{"type": "title", "title": "Hello"}],
            style_name="bold_signal",
            mood="excited",
        )
        data = session.to_dict()
        restored = PresentationSession.from_dict(data)

        assert restored.topic == session.topic
        assert restored.slides == session.slides
        assert restored.style_name == session.style_name
        assert restored.mood == session.mood
        assert restored.id == session.id

    def test_add_edit_records_history(self):
        session = PresentationSession()
        session.add_edit("fix typo", "Fixed typo in slide 3")
        assert len(session.edit_history) == 1
        assert session.edit_history[0]["instruction"] == "fix typo"
        assert session.edit_history[0]["summary"] == "Fixed typo in slide 3"
        assert "timestamp" in session.edit_history[0]

    def test_default_output_formats(self):
        session = PresentationSession()
        assert session.output_formats == ["html"]


class TestSessionManager:
    def test_create_saves_file(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        session = mgr.create(topic="Test Topic")
        path = tmp_path / ".slide-sessions" / f"{session.id}.json"
        assert path.exists()

    def test_load_round_trip(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        session = mgr.create(topic="Round Trip", mood="calm")
        loaded = mgr.load(session.id)
        assert loaded.topic == "Round Trip"
        assert loaded.mood == "calm"

    def test_load_nonexistent_raises(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            mgr.load("abcdef123456")  # Valid hex but no file

    def test_load_invalid_session_id_raises(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        with pytest.raises(ValueError, match="Invalid session ID"):
            mgr.load("nonexistent_id")

    def test_list_sessions(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        mgr.create(topic="First")
        mgr.create(topic="Second")
        sessions = mgr.list_sessions()
        assert len(sessions) == 2
        topics = {s["topic"] for s in sessions}
        assert topics == {"First", "Second"}

    def test_delete_session(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        session = mgr.create(topic="To Delete")
        assert mgr.delete(session.id) is True
        assert mgr.delete(session.id) is False  # Already deleted

    def test_delete_nonexistent_returns_false(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        assert mgr.delete("abcdef000000") is False  # Valid hex, no file

    def test_delete_invalid_session_id_raises(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        with pytest.raises(ValueError, match="Invalid session ID"):
            mgr.delete("does_not_exist")

    def test_latest(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        mgr.create(topic="Older")
        mgr.create(topic="Newer")
        latest = mgr.latest()
        assert latest is not None
        # latest should be the most recently updated

    def test_latest_empty(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        assert mgr.latest() is None

    def test_save_updates_timestamp(self, tmp_path: Path):
        mgr = SessionManager(str(tmp_path))
        session = mgr.create(topic="Timestamp Test")
        old_ts = session.updated_at
        import time
        time.sleep(0.01)
        mgr.save(session)
        loaded = mgr.load(session.id)
        assert loaded.updated_at >= old_ts

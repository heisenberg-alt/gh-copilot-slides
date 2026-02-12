"""Shared fixtures for the slide-builder test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRESETS_DIR = PROJECT_ROOT / "templates" / "presets"


@pytest.fixture()
def sample_slides() -> list[dict]:
    """Minimal valid slide list (title + content + closing)."""
    return [
        {"type": "title", "title": "Welcome", "subtitle": "A test deck"},
        {
            "type": "content",
            "title": "Key Points",
            "bullets": ["Point A", "Point B", "Point C"],
        },
        {"type": "closing", "title": "Thank You"},
    ]


@pytest.fixture()
def full_slide_set() -> list[dict]:
    """One slide of every supported type."""
    return [
        {"type": "title", "title": "Title Slide", "subtitle": "Subtitle"},
        {
            "type": "content",
            "title": "Content Slide",
            "bullets": ["Bullet 1", "Bullet 2"],
        },
        {
            "type": "feature_grid",
            "title": "Features",
            "cards": [
                {"title": "Card A", "description": "Desc A", "icon": "🚀"},
                {"title": "Card B", "description": "Desc B"},
            ],
        },
        {"type": "code", "title": "Code Slide", "code": 'print("hello")'},
        {
            "type": "quote",
            "title": "Quote Slide",
            "quote": "To be or not to be",
            "attribution": "Shakespeare",
        },
        {"type": "image", "title": "Image Slide", "image_src": "img.png"},
        {"type": "closing", "title": "Fin", "subtitle": "Goodbye"},
    ]


@pytest.fixture()
def sample_preset() -> dict:
    """Load bold_signal preset from disk."""
    path = PRESETS_DIR / "bold_signal.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def tmp_output(tmp_path: Path) -> Path:
    """Provide a temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out

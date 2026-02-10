"""
Slide Builder MCP — Style preset definitions.

Maps mood keywords to style presets and provides the preset catalog.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "presets"

# Mood → Preset mapping (same as SKILL.md)
MOOD_MAP: dict[str, list[str]] = {
    "impressed": ["bold_signal", "electric_studio", "dark_botanical"],
    "confident": ["bold_signal", "electric_studio", "dark_botanical"],
    "excited": ["creative_voltage", "neon_cyber", "split_pastel"],
    "energized": ["creative_voltage", "neon_cyber", "split_pastel"],
    "calm": ["notebook_tabs", "vintage_editorial", "pastel_geometry"],
    "focused": ["notebook_tabs", "vintage_editorial", "pastel_geometry"],
    "inspired": ["dark_botanical", "vintage_editorial", "pastel_geometry"],
    "moved": ["dark_botanical", "vintage_editorial", "pastel_geometry"],
    "professional": ["bold_signal", "notebook_tabs", "electric_studio"],
    "playful": ["creative_voltage", "split_pastel", "pastel_geometry"],
    "technical": ["terminal_green", "neon_cyber", "electric_studio"],
    "elegant": ["dark_botanical", "vintage_editorial", "notebook_tabs"],
}

ALL_PRESET_NAMES: list[str] = [
    "bold_signal",
    "electric_studio",
    "creative_voltage",
    "dark_botanical",
    "notebook_tabs",
    "pastel_geometry",
    "split_pastel",
    "vintage_editorial",
    "neon_cyber",
    "terminal_green",
]


def load_preset(name: str) -> dict[str, Any]:
    """Load a single preset by name. Raises FileNotFoundError if not found."""
    path = PRESETS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Preset '{name}' not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_presets() -> dict[str, dict[str, Any]]:
    """Load all presets from the templates/presets directory."""
    presets: dict[str, dict[str, Any]] = {}
    for name in ALL_PRESET_NAMES:
        try:
            presets[name] = load_preset(name)
        except FileNotFoundError:
            continue
    return presets


def presets_for_mood(mood: str) -> list[str]:
    """Return up to 3 preset names matching the given mood keyword."""
    mood_lower = mood.lower().strip()
    if mood_lower in MOOD_MAP:
        return MOOD_MAP[mood_lower]
    # Fuzzy fallback: check if mood is a substring of any key
    for key, presets in MOOD_MAP.items():
        if mood_lower in key or key in mood_lower:
            return presets
    # Default: one from each category
    return ["bold_signal", "notebook_tabs", "neon_cyber"]


def list_presets_summary() -> list[dict[str, str]]:
    """Return a condensed list of all presets for display."""
    summaries = []
    for name in ALL_PRESET_NAMES:
        try:
            p = load_preset(name)
            summaries.append({
                "name": name,
                "display_name": p["display_name"],
                "category": p["category"],
                "vibe": p["vibe"],
                "description": p["description"],
            })
        except FileNotFoundError:
            continue
    return summaries

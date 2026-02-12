"""Tests for slide_mcp.styles — preset loading and mood mapping."""

from __future__ import annotations

import pytest

from slide_mcp.styles import (
    ALL_PRESET_NAMES,
    MOOD_MAP,
    list_presets_summary,
    load_all_presets,
    load_preset,
    presets_for_mood,
)


class TestLoadPreset:
    def test_load_existing_preset(self):
        preset = load_preset("bold_signal")
        assert preset["name"] == "bold_signal"
        assert "colors" in preset
        assert "fonts" in preset

    def test_load_all_known_presets(self):
        for name in ALL_PRESET_NAMES:
            preset = load_preset(name)
            assert preset["display_name"]

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_preset("does_not_exist_xyz")


class TestLoadAllPresets:
    def test_returns_all(self):
        presets = load_all_presets()
        assert len(presets) == len(ALL_PRESET_NAMES)

    def test_all_presets_have_required_keys(self):
        presets = load_all_presets()
        for name, preset in presets.items():
            assert "display_name" in preset, f"{name} missing display_name"
            assert "colors" in preset, f"{name} missing colors"
            assert "fonts" in preset, f"{name} missing fonts"


class TestPresetsForMood:
    def test_exact_mood_match(self):
        result = presets_for_mood("excited")
        assert result == MOOD_MAP["excited"]

    def test_case_insensitive(self):
        result = presets_for_mood("EXCITED")
        assert result == MOOD_MAP["excited"]

    def test_unknown_mood_returns_defaults(self):
        result = presets_for_mood("nonsensical_mood_xyz")
        assert len(result) == 3

    def test_substring_match(self):
        # "confiden" should match "confident" via substring
        result = presets_for_mood("confiden")
        assert result == MOOD_MAP["confident"]

    def test_returns_max_three(self):
        for mood in MOOD_MAP:
            result = presets_for_mood(mood)
            assert len(result) <= 3


class TestListPresetsSummary:
    def test_summary_count(self):
        summaries = list_presets_summary()
        assert len(summaries) == len(ALL_PRESET_NAMES)

    def test_summary_keys(self):
        summaries = list_presets_summary()
        for s in summaries:
            assert "name" in s
            assert "display_name" in s
            assert "category" in s
            assert "vibe" in s
            assert "description" in s

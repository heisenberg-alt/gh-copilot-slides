"""Tests for slide_mcp.utils — escape_html and validate_slides."""

from __future__ import annotations

import pytest

from slide_mcp.utils import VALID_SLIDE_TYPES, escape_html, validate_slides


# ── escape_html ──────────────────────────────────────────────────────────


class TestEscapeHtml:
    def test_plain_text_unchanged(self):
        assert escape_html("hello world") == "hello world"

    def test_ampersand(self):
        assert escape_html("A & B") == "A &amp; B"

    def test_angle_brackets(self):
        assert escape_html("<script>alert('xss')</script>") == (
            "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )

    def test_quotes(self):
        assert escape_html('"hello"') == "&quot;hello&quot;"

    def test_empty_string(self):
        assert escape_html("") == ""

    def test_already_escaped(self):
        # Double-escaping is expected — the function is idempotent-safe
        assert escape_html("&amp;") == "&amp;amp;"


# ── validate_slides ─────────────────────────────────────────────────────


class TestValidateSlides:
    def test_empty_list(self):
        assert validate_slides([]) == []

    def test_valid_slides_unchanged(self):
        slides = [
            {"type": "title", "title": "Hello"},
            {"type": "content", "title": "Body"},
            {"type": "closing", "title": "Bye"},
        ]
        result = validate_slides(slides)
        assert result[0]["type"] == "title"
        assert result[-1]["type"] == "closing"

    def test_invalid_type_replaced(self):
        slides = [
            {"type": "title", "title": "Start"},
            {"type": "nonexistent", "title": "Mid"},
            {"type": "closing", "title": "End"},
        ]
        result = validate_slides(slides)
        assert result[1]["type"] == "content"

    def test_missing_title_gets_default(self):
        slides = [
            {"type": "title", "title": "Start"},
            {"type": "content"},
            {"type": "closing", "title": "End"},
        ]
        result = validate_slides(slides)
        assert result[1]["title"] == "Untitled Slide"

    def test_bullets_capped_at_six(self):
        slides = [
            {"type": "title", "title": "Start"},
            {
                "type": "content",
                "title": "Overflow",
                "bullets": [f"b{i}" for i in range(10)],
            },
            {"type": "closing", "title": "End"},
        ]
        result = validate_slides(slides)
        assert len(result[1]["bullets"]) == 6

    def test_cards_capped_at_six(self):
        slides = [
            {"type": "title", "title": "Start"},
            {
                "type": "feature_grid",
                "title": "Grid",
                "cards": [{"title": f"C{i}"} for i in range(8)],
            },
            {"type": "closing", "title": "End"},
        ]
        result = validate_slides(slides)
        assert len(result[1]["cards"]) == 6
        # Missing 'description' should be filled
        assert result[1]["cards"][0]["description"] == ""

    def test_first_slide_forced_to_title(self):
        slides = [
            {"type": "content", "title": "Not a title"},
            {"type": "closing", "title": "End"},
        ]
        result = validate_slides(slides)
        assert result[0]["type"] == "title"

    def test_last_slide_forced_to_closing(self):
        slides = [
            {"type": "title", "title": "Start"},
            {"type": "content", "title": "Content"},
        ]
        result = validate_slides(slides)
        assert result[-1]["type"] == "closing"

    def test_single_slide_is_both_title_and_closing(self):
        slides = [{"type": "content", "title": "Only"}]
        result = validate_slides(slides)
        # Single slide: forced to title first, then closing (closing wins as last check)
        assert result[0]["type"] == "closing"


class TestValidSlideTypes:
    def test_known_types(self):
        expected = {"title", "content", "feature_grid", "code", "quote", "image", "closing"}
        assert VALID_SLIDE_TYPES == expected

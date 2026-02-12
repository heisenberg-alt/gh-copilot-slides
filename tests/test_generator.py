"""Tests for slide_mcp.generator — HTML presentation generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from slide_mcp.generator import (
    _build_slide_html,
    generate_mood_previews,
    generate_presentation,
    generate_preview,
)


class TestBuildSlideHtml:
    def test_title_slide(self):
        html = _build_slide_html([{"type": "title", "title": "Hello", "subtitle": "World"}])
        assert "title-slide" in html
        assert "Hello" in html
        assert "World" in html

    def test_content_slide_with_bullets(self):
        html = _build_slide_html([
            {"type": "content", "title": "Points", "bullets": ["A", "B", "C"]},
        ])
        assert "content-slide" in html
        assert "<li" in html
        assert "A" in html

    def test_quote_slide(self):
        html = _build_slide_html([
            {"type": "quote", "title": "Q", "quote": "Be bold", "attribution": "Author"},
        ])
        assert "quote-slide" in html
        assert "Be bold" in html
        assert "Author" in html

    def test_code_slide_escapes(self):
        html = _build_slide_html([
            {"type": "code", "title": "Code", "code": "<script>alert(1)</script>"},
        ])
        assert "code-slide" in html
        assert "<script>" not in html  # Should be escaped
        assert "&lt;script&gt;" in html

    def test_feature_grid_slide(self):
        html = _build_slide_html([
            {
                "type": "feature_grid",
                "title": "Features",
                "cards": [
                    {"title": "Fast", "description": "Very fast", "icon": "⚡"},
                    {"title": "Safe", "description": "Very safe"},
                ],
            },
        ])
        assert "feature_grid-slide" in html
        assert "Fast" in html
        assert "⚡" in html

    def test_image_slide(self):
        html = _build_slide_html([
            {"type": "image", "title": "Photo", "image_src": "photo.png"},
        ])
        assert "image-slide" in html
        assert "photo.png" in html

    def test_closing_slide(self):
        html = _build_slide_html([
            {"type": "closing", "title": "Thanks", "subtitle": "Goodbye"},
        ])
        assert "closing-slide" in html
        assert "Thanks" in html

    def test_unknown_type_uses_default_rendering(self):
        html = _build_slide_html([
            {"type": "unknown_type", "title": "Fallback"},
        ])
        # Unknown types fall through to the default (content) branch
        assert "slide-content" in html
        assert "Fallback" in html

    def test_xss_in_title(self):
        html = _build_slide_html([
            {"type": "content", "title": "<img onerror=alert(1)>"},
        ])
        assert "<img onerror" not in html
        assert "&lt;img onerror" in html

    def test_xss_in_bullets(self):
        html = _build_slide_html([
            {
                "type": "content",
                "title": "Safe",
                "bullets": ['<script>alert("xss")</script>'],
            },
        ])
        assert "<script>" not in html

    def test_bullets_capped_at_six_in_html(self):
        html = _build_slide_html([
            {
                "type": "content",
                "title": "Many",
                "bullets": [f"Item {i}" for i in range(10)],
            },
        ])
        assert html.count("<li") == 6

    def test_cards_capped_at_six(self):
        html = _build_slide_html([
            {
                "type": "feature_grid",
                "title": "Grid",
                "cards": [{"title": f"C{i}", "description": f"D{i}"} for i in range(10)],
            },
        ])
        assert html.count('class="card') == 6

    def test_empty_slides_list(self):
        html = _build_slide_html([])
        assert html.strip() == ""


class TestGeneratePresentation:
    def test_generates_html_file(self, sample_slides, tmp_output):
        out = str(tmp_output / "deck.html")
        result = generate_presentation("Test Deck", sample_slides, "bold_signal", out)
        assert Path(result).exists()
        content = Path(result).read_text()
        assert "<html" in content
        assert "Welcome" in content

    def test_output_contains_all_slides(self, full_slide_set, tmp_output):
        out = str(tmp_output / "full.html")
        result = generate_presentation("Full Deck", full_slide_set, "terminal_green", out)
        content = Path(result).read_text()
        assert "Title Slide" in content
        assert "Content Slide" in content
        assert "Features" in content
        assert "Code Slide" in content
        # Quote text is present ("To be or not to be")
        assert "To be or not to be" in content

    def test_invalid_preset_raises(self, sample_slides, tmp_output):
        with pytest.raises(FileNotFoundError):
            generate_presentation("Bad", sample_slides, "no_such_preset", str(tmp_output / "x.html"))


class TestGeneratePreview:
    def test_generates_preview_file(self, tmp_output):
        out = str(tmp_output / "preview.html")
        result = generate_preview("bold_signal", out)
        assert Path(result).exists()
        content = Path(result).read_text()
        assert "Bold Signal" in content

    def test_custom_text(self, tmp_output):
        out = str(tmp_output / "custom.html")
        result = generate_preview(
            "neon_cyber", out,
            preview_title="Custom Title",
            preview_subtitle="Custom Sub",
        )
        content = Path(result).read_text()
        assert "Custom Title" in content
        assert "Custom Sub" in content


class TestGenerateMoodPreviews:
    def test_returns_three_previews(self, tmp_output):
        results = generate_mood_previews("excited", str(tmp_output))
        assert len(results) == 3
        for r in results:
            assert Path(r["path"]).exists()
            assert "name" in r
            assert "display_name" in r

    def test_preview_files_are_distinct(self, tmp_output):
        results = generate_mood_previews("calm", str(tmp_output))
        paths = [r["path"] for r in results]
        assert len(set(paths)) == 3

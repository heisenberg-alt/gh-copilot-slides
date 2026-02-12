"""Tests for slide_mcp.ppt_converter — layout detection."""

from __future__ import annotations

import pytest

from slide_mcp.ppt_converter import _detect_layout


class _FakeSlideLayout:
    """Stub for pptx slide layout."""
    def __init__(self, name: str):
        self.name = name


class _FakeSlide:
    """Stub for pptx slide with a layout."""
    def __init__(self, layout_name: str):
        self.slide_layout = _FakeSlideLayout(layout_name)


class TestDetectLayout:
    def test_title_only(self):
        slide = _FakeSlide("Title Only")
        assert _detect_layout(slide) == "title"

    def test_title_slide(self):
        slide = _FakeSlide("Title Slide")
        assert _detect_layout(slide) == "title"

    def test_blank(self):
        slide = _FakeSlide("Blank")
        assert _detect_layout(slide) == "blank"

    def test_two_content(self):
        slide = _FakeSlide("Two Content")
        assert _detect_layout(slide) == "two_column"

    def test_comparison(self):
        slide = _FakeSlide("Comparison")
        assert _detect_layout(slide) == "two_column"

    def test_content(self):
        slide = _FakeSlide("Content with Caption")
        assert _detect_layout(slide) == "content"

    def test_default_content(self):
        slide = _FakeSlide("Custom Layout XYZ")
        assert _detect_layout(slide) == "content"

    def test_no_layout_attribute(self):
        """Gracefully handle slides with broken layouts."""
        class BrokenSlide:
            @property
            def slide_layout(self):
                raise AttributeError("no layout")

        result = _detect_layout(BrokenSlide())
        assert result == "content"

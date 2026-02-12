"""Tests for slide_mcp.agents.base — AgentResult and ConversationContext."""

from __future__ import annotations

import pytest

from slide_mcp.agents.base import AgentResult, ConversationContext


class TestAgentResult:
    def test_success_result(self):
        result = AgentResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_failure_result(self):
        result = AgentResult(success=False, error="Something failed")
        assert result.success is False
        assert result.error == "Something failed"

    def test_default_fields(self):
        result = AgentResult(success=True)
        assert result.data == {}
        assert result.messages == []
        assert result.error is None


class TestConversationContext:
    def test_default_values(self):
        ctx = ConversationContext()
        assert ctx.topic == ""
        assert ctx.slide_count == 10
        assert ctx.output_formats == ["html"]
        assert ctx.slides == []
        assert ctx.edit_instruction == ""

    def test_to_dict_round_trip(self):
        ctx = ConversationContext(
            topic="AI",
            mood="excited",
            slides=[{"type": "title", "title": "Test"}],
            style_name="bold_signal",
            edit_instruction="fix typos",
        )
        data = ctx.to_dict()
        restored = ConversationContext.from_dict(data)

        assert restored.topic == "AI"
        assert restored.mood == "excited"
        assert restored.slides == ctx.slides
        assert restored.style_name == "bold_signal"
        assert restored.edit_instruction == "fix typos"

    def test_to_dict_contains_all_fields(self):
        ctx = ConversationContext()
        data = ctx.to_dict()
        expected_keys = {
            "topic", "purpose", "urls", "files", "slide_count",
            "mood", "audience", "extra_instructions",
            "research_data", "slides", "presentation_title",
            "style_name", "style_recommendations", "custom_preset",
            "pptx_template_path", "output_dir", "output_formats",
            "output_paths", "edit_history", "edit_instruction",
        }
        assert set(data.keys()) == expected_keys

    def test_from_dict_ignores_unknown_keys(self):
        data = {"topic": "Test", "unknown_field": "should be ignored"}
        ctx = ConversationContext.from_dict(data)
        assert ctx.topic == "Test"
        assert not hasattr(ctx, "unknown_field") or ctx.__dict__.get("unknown_field") is None

    def test_edit_instruction_field(self):
        ctx = ConversationContext()
        ctx.edit_instruction = "make it funnier"
        assert ctx.edit_instruction == "make it funnier"
        data = ctx.to_dict()
        assert data["edit_instruction"] == "make it funnier"

    def test_output_formats_default_mutable(self):
        """Ensure default list is not shared between instances."""
        ctx1 = ConversationContext()
        ctx2 = ConversationContext()
        ctx1.output_formats.append("pptx")
        assert "pptx" not in ctx2.output_formats

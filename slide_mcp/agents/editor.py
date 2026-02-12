"""
Editor Agent — post-generation editing of slide content.

Accepts natural language edit instructions and modifies the slides list
accordingly: reorder, add, remove, change types, refine wording, etc.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import Agent, AgentResult, ConversationContext
from ..utils import validate_slides

logger = logging.getLogger("slide-builder.agents.editor")


class EditorAgent(Agent):
    """Edits existing slides based on natural language instructions."""

    name = "editor"
    description = "Modifies slides based on natural language edit instructions."

    def run(self, context: ConversationContext) -> AgentResult:
        instruction = context.edit_instruction
        if not instruction:
            return AgentResult(
                success=False,
                error="No edit instruction provided.",
            )

        if not context.slides:
            return AgentResult(
                success=False,
                error="No slides to edit. Generate slides first.",
            )

        self._log(f"Editing slides: {instruction}")

        try:
            updated_slides, change_summary = self._apply_edit(
                context.slides, instruction, context
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Edit failed: {e}",
            )

        return AgentResult(
            success=True,
            data={
                "slides": updated_slides,
                "change_summary": change_summary,
                "edit_instruction": instruction,
            },
            messages=[change_summary],
        )

    def _apply_edit(
        self,
        slides: list[dict[str, Any]],
        instruction: str,
        context: ConversationContext,
    ) -> tuple[list[dict[str, Any]], str]:
        """Use LLM to interpret the edit instruction and return modified slides."""

        current_slides_json = json.dumps(slides, indent=2)

        system_prompt = """You are a presentation editor. Given the current slides and an edit instruction,
return the modified slides array.

You can:
- Edit specific slide content (text, bullets, titles)
- Change slide types (e.g., content → quote, content → feature_grid)
- Add new slides at specific positions
- Remove slides
- Reorder slides
- Expand or compress content
- Improve wording and structure
- Add or modify speaker notes

Return a JSON object with:
{
  "slides": [...],  // The complete updated slides array
  "summary": "Brief description of changes made"
}

Rules:
- First slide must remain type "title"
- Last slide must remain type "closing"
- Keep the same slide schema: type, title, subtitle, bullets, cards, code, quote, attribution, speaker_notes
- Max 6 bullets per slide, max 6 cards per feature_grid
- Return ALL slides (modified and unmodified)"""

        user_prompt = f"""Current slides ({len(slides)} total):
{current_slides_json}

Edit instruction: {instruction}

Apply the edit and return the complete updated slides array."""

        result = self.llm.generate_json(system_prompt, user_prompt, temperature=0.3)

        if "slides" in result:
            updated_slides = result["slides"]
            summary = result.get("summary", "Slides updated")
        elif isinstance(result, list):
            updated_slides = result
            summary = "Slides updated"
        else:
            raise ValueError("Unexpected response format from LLM")

        # Validate
        updated_slides = validate_slides(updated_slides)
        return updated_slides, summary

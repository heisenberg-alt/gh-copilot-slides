"""
Curator Agent — transforms research data into structured slide content.

Takes the research bundle from the Research Agent and creates a coherent
narrative arc with properly typed slides matching the generator schema.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import Agent, AgentResult, ConversationContext
from ..utils import VALID_SLIDE_TYPES, validate_slides

logger = logging.getLogger("slide-builder.agents.curator")


class CuratorAgent(Agent):
    """Transforms research into structured, presentation-ready slide content."""

    name = "curator"
    description = "Organizes research into a coherent narrative with properly structured slides."

    def run(self, context: ConversationContext) -> AgentResult:
        self._log(f"Curating {context.slide_count} slides for: {context.topic}")

        research = context.research_data
        if not research:
            return AgentResult(
                success=False,
                error="No research data available. Run the Research Agent first.",
            )

        try:
            slides = self._curate_slides(context, research)
            # Validate and fix slide structure
            slides = validate_slides(slides)
            title = self._determine_title(context, research, slides)
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Curation failed: {e}",
            )

        return AgentResult(
            success=True,
            data={
                "slides": slides,
                "presentation_title": title,
                "slide_count": len(slides),
            },
            messages=[
                f"Created {len(slides)} slides",
                f"Title: {title}",
                f"Slide types: {', '.join(s.get('type', 'content') for s in slides)}",
            ],
        )

    def _curate_slides(
        self, context: ConversationContext, research: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Use LLM to create slides from research data."""

        system_prompt = """You are an expert presentation curator. Transform research data into
a structured slide deck.

Return a JSON array where each slide object has these fields:
- "type": one of "title", "content", "feature_grid", "code", "quote", "image", "closing"
- "title": the slide heading (required)
- "subtitle": optional subtitle text
- "bullets": optional array of bullet points (max 6, keep each to 1-2 lines)
- "cards": optional array of {"title", "description", "icon"} for feature_grid (max 6)
- "code": optional code string for code slides
- "quote": optional quote text for quote slides
- "attribution": optional attribution for quote slides
- "speaker_notes": optional notes for the presenter

Rules:
1. First slide MUST be type "title" with a compelling title and subtitle
2. Last slide MUST be type "closing" with a memorable takeaway
3. Use "feature_grid" for comparisons, features, or categorized information
4. Use "quote" for impactful quotes from the research (with attribution)
5. Use "content" with bullets for most informational slides
6. Keep bullets concise — max 6 per slide, 1-2 lines each
7. Create a clear narrative arc: intro → context → body → implications → conclusion
8. Include speaker_notes with talking points for each slide
9. Ensure information density is appropriate — not too sparse, not too crowded
10. Use data and statistics where available from the research

Return ONLY the JSON array."""

        # Build research summary for the prompt
        research_summary = self._format_research_for_prompt(research)

        user_prompt = f"""Create a {context.slide_count}-slide {context.purpose} presentation.

Topic: {context.topic}
Target audience: {context.audience or 'General professional audience'}
Desired mood/feeling: {context.mood or 'Professional'}
Extra instructions: {context.extra_instructions or 'None'}

Research data:
{research_summary}

Generate exactly {context.slide_count} slides with a compelling narrative arc."""

        raw = self.llm.generate(system_prompt, user_prompt, temperature=0.5)
        return self._parse_slides_response(raw)

    def _format_research_for_prompt(self, research: dict[str, Any]) -> str:
        """Format research bundle into a prompt-friendly string."""
        parts = []

        if research.get("narrative_arc"):
            parts.append(f"Suggested narrative: {research['narrative_arc']}")

        if research.get("key_themes"):
            parts.append(f"Key themes: {', '.join(research['key_themes'])}")

        if research.get("key_facts"):
            facts = research["key_facts"][:10]
            parts.append("Key facts:")
            for f in facts:
                importance = f.get("importance", "medium")
                parts.append(f"  [{importance}] {f.get('fact', '')} (Source: {f.get('source', 'N/A')})")

        if research.get("statistics"):
            parts.append("Statistics:")
            for s in research["statistics"][:5]:
                parts.append(f"  • {s.get('stat', '')} — {s.get('context', '')}")

        if research.get("quotes"):
            parts.append("Notable quotes:")
            for q in research["quotes"][:4]:
                parts.append(f'  "{q.get("quote", "")}" — {q.get("attribution", "Unknown")}')

        if research.get("sections"):
            parts.append("Research sections:")
            for sec in research["sections"][:7]:
                parts.append(f"  ## {sec.get('heading', '')}")
                parts.append(f"  {sec.get('summary', '')}")
                for kp in sec.get("key_points", [])[:3]:
                    parts.append(f"    • {kp}")

        if research.get("audience_insights"):
            parts.append(f"Audience insights: {research['audience_insights']}")

        return "\n".join(parts)

    def _parse_slides_response(self, raw: str) -> list[dict[str, Any]]:
        """Parse the LLM's slide JSON response."""
        cleaned = raw.strip()
        # Strip markdown fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "slides" in result:
                return result["slides"]
            return [result]
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse slides from response: {raw[:300]}...")

    def _determine_title(
        self,
        context: ConversationContext,
        research: dict[str, Any],
        slides: list[dict[str, Any]],
    ) -> str:
        """Determine the presentation title."""
        # Use the title slide's title
        if slides and slides[0].get("title"):
            return slides[0]["title"]
        # Use research suggestion
        if research.get("title_suggestion"):
            return research["title_suggestion"]
        # Fall back to topic
        return context.topic

"""
Style Recommender Agent — analyzes content and recommends visual styles.

Uses existing preset data and mood mappings, enhanced with LLM analysis
of content tone. Can also extract custom presets from user-provided PPTX templates.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .base import Agent, AgentResult, ConversationContext

logger = logging.getLogger("slide-builder.agents.style_recommender")


class StyleRecommenderAgent(Agent):
    """Recommends visual styles based on content analysis and mood."""

    name = "style_recommender"
    description = "Analyzes content tone and recommends the best visual style preset."

    def run(self, context: ConversationContext) -> AgentResult:
        self._log(f"Recommending styles for: {context.topic}")

        from ..styles import load_preset, load_all_presets, presets_for_mood

        # If user already specified a style, validate and return it
        if context.style_name:
            try:
                preset = load_preset(context.style_name)
                return AgentResult(
                    success=True,
                    data={
                        "recommended_style": context.style_name,
                        "recommendations": [{
                            "name": context.style_name,
                            "display_name": preset["display_name"],
                            "vibe": preset["vibe"],
                            "reason": "User-selected style",
                            "confidence": 1.0,
                        }],
                    },
                    messages=[f"Using user-selected style: {context.style_name}"],
                )
            except FileNotFoundError:
                self._log(f"User-specified style '{context.style_name}' not found, recommending alternatives")

        # If user provided a PPTX template, extract its theme
        if context.pptx_template_path:
            try:
                custom_preset = self._extract_pptx_theme(context.pptx_template_path)
                return AgentResult(
                    success=True,
                    data={
                        "recommended_style": "custom",
                        "custom_preset": custom_preset,
                        "recommendations": [{
                            "name": "custom",
                            "display_name": "Custom (from PPTX template)",
                            "vibe": "Matched to your template",
                            "reason": "Extracted from provided PPTX template",
                            "confidence": 0.9,
                        }],
                    },
                    messages=["Extracted custom theme from PPTX template"],
                )
            except Exception as e:
                self._log(f"PPTX theme extraction failed: {e}")

        # If mood is provided, use mood mapping + LLM refinement
        if context.mood:
            mood_presets = presets_for_mood(context.mood)
        else:
            mood_presets = None

        # Use LLM to analyze content and recommend styles
        try:
            recommendations = self._analyze_and_recommend(context, mood_presets)
        except Exception as e:
            # Fallback to mood-based or default
            self._log(f"LLM recommendation failed: {e}, using fallback")
            if mood_presets:
                recommendations = self._build_fallback_recommendations(mood_presets)
            else:
                recommendations = self._build_fallback_recommendations(
                    ["bold_signal", "notebook_tabs", "neon_cyber"]
                )

        top_style = recommendations[0]["name"] if recommendations else "bold_signal"

        return AgentResult(
            success=True,
            data={
                "recommended_style": top_style,
                "recommendations": recommendations,
            },
            messages=[
                f"Top recommendation: {top_style}",
                f"Alternatives: {', '.join(r['name'] for r in recommendations[1:])}",
            ],
        )

    def _analyze_and_recommend(
        self,
        context: ConversationContext,
        mood_presets: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Use LLM to analyze content and recommend styles."""
        from ..styles import load_all_presets

        all_presets = load_all_presets()

        # Build a summary of available styles
        styles_summary = []
        for name, preset in all_presets.items():
            styles_summary.append(
                f"  {name}: {preset['display_name']} — {preset['vibe']} "
                f"(category: {preset['category']})"
            )

        system_prompt = """You are a presentation design expert. Analyze the presentation context
and recommend the 3 best style presets from the available options.

Return a JSON array of 3 recommendations:
[
  {
    "name": "preset_name",
    "reason": "Why this style fits the content and audience",
    "confidence": 0.95
  },
  ...
]

Consider: topic gravity, audience expectations, content type (technical vs creative),
and desired emotional impact. Order by best fit (highest confidence first)."""

        # Build context for analysis
        research_summary = ""
        if context.research_data:
            themes = context.research_data.get("key_themes", [])
            if themes:
                research_summary = f"Key themes: {', '.join(themes)}"
            arc = context.research_data.get("narrative_arc", "")
            if arc:
                research_summary += f"\nNarrative arc: {arc}"

        user_prompt = f"""Topic: {context.topic}
Purpose: {context.purpose}
Audience: {context.audience or 'General'}
Desired mood: {context.mood or 'Not specified'}
{research_summary}

{f"Mood-matched presets (prioritize these): {', '.join(mood_presets)}" if mood_presets else ""}

Available styles:
{chr(10).join(styles_summary)}"""

        raw = self.llm.generate(system_prompt, user_prompt, temperature=0.3)

        # Parse response
        recs = self._parse_recommendations(raw, all_presets)
        return recs

    def _parse_recommendations(
        self, raw: str, all_presets: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Parse LLM recommendations and enrich with preset data."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            recs = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1:
                try:
                    recs = json.loads(cleaned[start:end + 1])
                except json.JSONDecodeError:
                    return self._build_fallback_recommendations(
                        ["bold_signal", "notebook_tabs", "neon_cyber"]
                    )
            else:
                return self._build_fallback_recommendations(
                    ["bold_signal", "notebook_tabs", "neon_cyber"]
                )

        enriched = []
        for rec in recs[:3]:
            name = rec.get("name", "")
            if name in all_presets:
                preset = all_presets[name]
                enriched.append({
                    "name": name,
                    "display_name": preset["display_name"],
                    "vibe": preset["vibe"],
                    "category": preset["category"],
                    "reason": rec.get("reason", ""),
                    "confidence": rec.get("confidence", 0.5),
                })

        if not enriched:
            return self._build_fallback_recommendations(
                ["bold_signal", "notebook_tabs", "neon_cyber"]
            )
        return enriched

    def _build_fallback_recommendations(
        self, preset_names: list[str]
    ) -> list[dict[str, Any]]:
        """Build recommendations from preset names without LLM."""
        from ..styles import load_preset

        recs = []
        for name in preset_names[:3]:
            try:
                preset = load_preset(name)
                recs.append({
                    "name": name,
                    "display_name": preset["display_name"],
                    "vibe": preset["vibe"],
                    "category": preset["category"],
                    "reason": "Default recommendation based on mood mapping",
                    "confidence": 0.5,
                })
            except FileNotFoundError:
                continue
        return recs

    def _extract_pptx_theme(self, pptx_path: str) -> dict[str, Any]:
        """Extract color scheme and fonts from a PPTX template to create a custom preset."""
        try:
            from pptx import Presentation
            from pptx.util import Pt
            from pptx.dml.color import RGBColor
        except ImportError:
            raise ImportError("python-pptx required: pip install python-pptx")

        prs = Presentation(pptx_path)
        theme = prs.slide_masters[0].slide_layouts[0]

        # Extract theme colors
        colors = {
            "bg_primary": "#1a1a2e",
            "text_primary": "#ffffff",
            "text_secondary": "#b0b0b0",
            "accent": "#e94560",
        }

        # Try to extract from theme XML
        try:
            slide_master = prs.slide_masters[0]
            # Access theme element
            theme_elem = slide_master.element
            # Look for color scheme in the XML
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            color_scheme = theme_elem.findall(".//a:clrScheme//*", ns)
            color_map = {}
            for elem in color_scheme:
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                # Get srgbClr or sysClr
                srgb = elem.find("{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
                if srgb is not None:
                    color_map[tag] = f"#{srgb.get('val', '000000')}"

            if color_map:
                colors["bg_primary"] = color_map.get("dk1", colors["bg_primary"])
                colors["text_primary"] = color_map.get("lt1", colors["text_primary"])
                colors["accent"] = color_map.get("accent1", colors["accent"])
                colors["text_secondary"] = color_map.get("dk2", colors["text_secondary"])
        except Exception:
            pass  # Use defaults

        # Extract fonts
        fonts = {
            "display": {"family": "Inter", "weights": [700, 900], "source": "google"},
            "body": {"family": "Inter", "weights": [400, 500], "source": "google"},
        }

        try:
            theme_elem = prs.slide_masters[0].element
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            major_font = theme_elem.find(".//a:majorFont/a:latin", ns)
            minor_font = theme_elem.find(".//a:minorFont/a:latin", ns)
            if major_font is not None:
                fonts["display"]["family"] = major_font.get("typeface", "Inter")
            if minor_font is not None:
                fonts["body"]["family"] = minor_font.get("typeface", "Inter")
        except Exception:
            pass

        # Build font import URL
        display_font = fonts["display"]["family"].replace(" ", "+")
        body_font = fonts["body"]["family"].replace(" ", "+")
        font_import = f"https://fonts.googleapis.com/css2?family={display_font}:wght@400;700;900&family={body_font}:wght@400;500&display=swap"

        return {
            "name": "custom_template",
            "display_name": f"Custom ({Path(pptx_path).stem})",
            "category": "custom",
            "vibe": "Matched to your PPTX template",
            "description": f"Theme extracted from {Path(pptx_path).name}",
            "fonts": fonts,
            "colors": colors,
            "signature_elements": [],
            "font_import": font_import,
            "extra_css": "",
        }

"""
Shared utilities — HTML escaping, slide validation, and common helpers.
"""

from __future__ import annotations

import html
from typing import Any

# Valid slide types matching the generator schema
VALID_SLIDE_TYPES = {"title", "content", "feature_grid", "code", "quote", "image", "closing"}


def escape_html(text: str) -> str:
    """Escape HTML special characters in user-provided text.

    Prevents XSS when rendering untrusted content (e.g., from PPTX files)
    into HTML presentations.
    """
    return html.escape(text, quote=True)


def validate_slides(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and fix slide structure.

    Ensures each slide has a valid type, a title, and respects
    content limits (max 6 bullets, max 6 cards). Enforces that the
    first slide is type 'title' and the last is type 'closing'.

    Args:
        slides: List of slide dicts to validate.

    Returns:
        The validated (and possibly corrected) slides list.
    """
    if not slides:
        return slides

    for slide in slides:
        # Ensure valid type
        if slide.get("type") not in VALID_SLIDE_TYPES:
            slide["type"] = "content"

        # Ensure title exists
        if not slide.get("title"):
            slide["title"] = "Untitled Slide"

        # Limit bullets
        if slide.get("bullets"):
            slide["bullets"] = slide["bullets"][:6]

        # Limit cards
        if slide.get("cards"):
            slide["cards"] = slide["cards"][:6]
            for card in slide["cards"]:
                if "title" not in card:
                    card["title"] = ""
                if "description" not in card:
                    card["description"] = ""

    # Ensure first slide is title
    if slides[0].get("type") != "title":
        slides[0]["type"] = "title"

    # Ensure last slide is closing
    if slides[-1].get("type") != "closing":
        slides[-1]["type"] = "closing"

    return slides

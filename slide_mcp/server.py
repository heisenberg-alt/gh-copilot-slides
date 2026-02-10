"""
Slide Builder MCP Server.

An MCP (Model Context Protocol) server that provides tools for creating
stunning HTML presentations. Works with VS Code Copilot agent mode,
Claude Code, Cursor, and any other MCP-compatible client.

Tools:
  - list_styles          : List all available style presets
  - get_style_details    : Get full config for a specific preset
  - preview_styles       : Generate 3 style preview HTML files by mood
  - create_presentation  : Generate a full HTML presentation
  - convert_ppt          : Convert a .pptx file to HTML presentation
  - summarize_ppt        : Extract and summarize PPT content for review

Resources:
  - preset://{name}      : Read a style preset's full config
  - template://base      : Read the base HTML template
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .generator import (
    generate_mood_previews,
    generate_presentation,
    generate_preview,
)
from .ppt_converter import extract_pptx, pptx_to_slides, summarize_extraction
from .styles import (
    ALL_PRESET_NAMES,
    load_all_presets,
    load_preset,
    list_presets_summary,
    presets_for_mood,
)

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "slide-builder",
    instructions=(
        "Create stunning, animation-rich HTML presentations from scratch "
        "or by converting PowerPoint files. Provides visual style discovery "
        "with 10 curated presets and mood-based selection."
    ),
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

logger = logging.getLogger("slide-builder-mcp")

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_styles() -> str:
    """
    List all 10 available style presets with their name, category, vibe, and description.

    Use this to show the user what styles are available before they choose one.
    Dark themes: bold_signal, electric_studio, creative_voltage, dark_botanical
    Light themes: notebook_tabs, pastel_geometry, split_pastel, vintage_editorial
    Specialty: neon_cyber, terminal_green
    """
    summaries = list_presets_summary()
    lines = ["# Available Style Presets\n"]

    current_category = ""
    for s in summaries:
        if s["category"] != current_category:
            current_category = s["category"]
            lines.append(f"\n## {current_category.title()} Themes\n")
        lines.append(f"**{s['display_name']}** (`{s['name']}`)")
        lines.append(f"  {s['vibe']}")
        lines.append(f"  _{s['description']}_\n")

    return "\n".join(lines)


@mcp.tool()
def get_style_details(style_name: str) -> str:
    """
    Get the full configuration for a specific style preset.

    Args:
        style_name: The preset name (e.g., 'bold_signal', 'neon_cyber').

    Returns:
        JSON string with full preset config including colors, fonts,
        signature elements, and CSS.
    """
    try:
        preset = load_preset(style_name)
        return json.dumps(preset, indent=2)
    except FileNotFoundError:
        available = ", ".join(ALL_PRESET_NAMES)
        return f"Error: Preset '{style_name}' not found. Available: {available}"


@mcp.tool()
def preview_styles(
    mood: str,
    output_dir: str,
    preview_title: str = "Your Presentation Title",
    preview_subtitle: str = "A beautiful slide deck crafted just for you",
) -> str:
    """
    Generate 3 style preview HTML files based on a mood keyword.

    This is the "show, don't tell" approach: instead of describing styles,
    generate visual previews the user can open in their browser.

    Mood keywords: impressed, confident, excited, energized, calm, focused,
    inspired, moved, professional, playful, technical, elegant.

    Args:
        mood: How the user wants their audience to feel.
        output_dir: Directory to write the 3 preview HTML files.
        preview_title: Title text shown in previews.
        preview_subtitle: Subtitle text shown in previews.

    Returns:
        Summary of generated previews with file paths.
    """
    results = generate_mood_previews(mood, output_dir, preview_title, preview_subtitle)

    lines = [f"Generated **3 style previews** for mood: _{mood}_\n"]
    for i, r in enumerate(results):
        label = chr(ord("A") + i)
        lines.append(f"**Style {label}: {r['display_name']}** — {r['vibe']}")
        lines.append(f"  File: `{r['path']}`\n")

    lines.append("Open each file in a browser to see them in action.")
    lines.append("Pick the one that resonates, or mix elements from multiple styles.")
    return "\n".join(lines)


@mcp.tool()
def create_presentation(
    title: str,
    slides: list[dict[str, Any]],
    style_name: str,
    output_path: str,
) -> str:
    """
    Generate a complete, self-contained HTML presentation.

    Each slide dict must have:
      - type: "title" | "content" | "feature_grid" | "code" | "quote" | "image" | "closing"
      - title: str (the heading)
      - subtitle: str (optional)
      - bullets: list[str] (optional, for content slides, max 6)
      - code: str (optional, for code slides)
      - quote: str (optional, for quote slides)
      - attribution: str (optional, for quote slides)
      - cards: list[{title, description, icon}] (optional, for feature_grid, max 6)
      - image_src: str (optional, for image slides)

    Content limits per slide (viewport fitting):
      - Title: 1 heading + 1 subtitle
      - Content: 1 heading + 4-6 bullets (max 2 lines each)
      - Feature grid: 1 heading + 6 cards (2x3 or 3x2)
      - Code: 1 heading + 8-10 lines of code
      - Quote: 1 quote (max 3 lines) + attribution

    Args:
        title: The presentation title (used in HTML <title>).
        slides: List of slide content dicts.
        style_name: Preset name (e.g., 'neon_cyber').
        output_path: File path for the generated HTML.

    Returns:
        Path to the generated presentation file with summary.
    """
    try:
        result_path = generate_presentation(title, slides, style_name, output_path)
        return (
            f"Presentation generated successfully!\n\n"
            f"📁 **File:** `{result_path}`\n"
            f"🎨 **Style:** {style_name}\n"
            f"📊 **Slides:** {len(slides)}\n\n"
            f"**Navigation:**\n"
            f"- Arrow keys (← →) or Space to navigate\n"
            f"- Scroll/swipe also works\n"
            f"- Click the dots on the right to jump to a slide\n\n"
            f"**To customize:**\n"
            f"- Colors: Edit `:root` CSS variables at the top\n"
            f"- Fonts: Change the Google Fonts/Fontshare link\n"
            f"- Animations: Modify `.reveal` class timings"
        )
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating presentation: {e}"


@mcp.tool()
def convert_ppt(
    pptx_path: str,
    style_name: str,
    output_path: str,
) -> str:
    """
    Convert a PowerPoint (.pptx) file to a styled HTML presentation.

    Extracts all text, images, and notes from the PPT, then generates
    an HTML presentation in the chosen style. Images are saved to an
    assets/ folder next to the output file.

    Args:
        pptx_path: Path to the .pptx file.
        style_name: Preset name for the HTML style.
        output_path: File path for the generated HTML.

    Returns:
        Summary of conversion with file path.
    """
    try:
        output_dir = str(Path(output_path).parent)
        slides = pptx_to_slides(pptx_path, output_dir)

        # Use first slide title as presentation title
        pres_title = slides[0]["title"] if slides and slides[0].get("title") else "Presentation"

        result_path = generate_presentation(pres_title, slides, style_name, output_path)
        return (
            f"PowerPoint converted successfully!\n\n"
            f"📁 **HTML:** `{result_path}`\n"
            f"🎨 **Style:** {style_name}\n"
            f"📊 **Slides:** {len(slides)}\n"
            f"🖼️ **Assets:** `{output_dir}/assets/`\n\n"
            f"All images from the PPT have been extracted and embedded.\n\n"
            f"**Navigation:**\n"
            f"- Arrow keys, scroll, or swipe to navigate\n"
            f"- Click navigation dots to jump to slides"
        )
    except ImportError as e:
        return str(e)
    except Exception as e:
        return f"Error converting PPT: {e}"


@mcp.tool()
def summarize_ppt(pptx_path: str, output_dir: str) -> str:
    """
    Extract and summarize a PowerPoint file's content for user review.

    Use this before convert_ppt to let the user confirm the extracted
    content and choose a style.

    Args:
        pptx_path: Path to the .pptx file.
        output_dir: Directory for extracted assets.

    Returns:
        Human-readable summary of all slides and their content.
    """
    try:
        return summarize_extraction(pptx_path, output_dir)
    except ImportError as e:
        return str(e)
    except Exception as e:
        return f"Error reading PPT: {e}"


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("preset://{name}")
def read_preset(name: str) -> str:
    """Read a style preset's full configuration as JSON."""
    try:
        preset = load_preset(name)
        return json.dumps(preset, indent=2)
    except FileNotFoundError:
        return json.dumps({"error": f"Preset '{name}' not found"})


@mcp.resource("template://base")
def read_base_template() -> str:
    """Read the base HTML template."""
    return (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")


@mcp.resource("template://preview")
def read_preview_template() -> str:
    """Read the preview HTML template."""
    return (TEMPLATES_DIR / "preview.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Prompts (pre-built conversation starters)
# ---------------------------------------------------------------------------


@mcp.prompt()
def new_presentation() -> str:
    """Start creating a new presentation from scratch."""
    return (
        "I want to create a new HTML presentation. Please help me through the process:\n\n"
        "1. First, ask me about the purpose, length, and content of my presentation.\n"
        "2. Then, ask how I want my audience to feel (impressed, excited, calm, etc.).\n"
        "3. Use preview_styles to generate 3 visual style options for me to compare.\n"
        "4. Once I pick a style, use create_presentation to generate the full deck.\n\n"
        "Let's start — what is this presentation for?"
    )


@mcp.prompt()
def convert_powerpoint() -> str:
    """Convert an existing PowerPoint to a web presentation."""
    return (
        "I want to convert a PowerPoint file to a beautiful web presentation.\n\n"
        "1. First, use summarize_ppt to extract and show me the content.\n"
        "2. Ask me to confirm the extracted content looks correct.\n"
        "3. Then ask how I want my audience to feel, and generate style previews.\n"
        "4. Once I pick a style, use convert_ppt to generate the HTML.\n\n"
        "Please provide the path to your .pptx file."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

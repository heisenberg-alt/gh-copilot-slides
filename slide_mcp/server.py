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

# Agent orchestrator imports (lazy — only loaded when agent tools are called)
_orchestrator = None


def _get_orchestrator():
    """Lazy-load the orchestrator (avoids import cost on every server start)."""
    global _orchestrator
    if _orchestrator is None:
        from .agents.orchestrator import Orchestrator
        _orchestrator = Orchestrator()
    return _orchestrator

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
def research_and_present() -> str:
    """Create a research-driven presentation with AI agent team."""
    return (
        "I want to create a research-driven presentation using the AI agent pipeline.\n\n"
        "This will:\n"
        "1. **Research** — Gather content from URLs, web search, and local files\n"
        "2. **Curate** — Structure the research into compelling slides\n"
        "3. **Style** — Recommend the best visual theme\n"
        "4. **Generate** — Output in your preferred formats (HTML, PPTX, PDF)\n"
        "5. **Edit** — Iteratively refine until you're satisfied\n\n"
        "Please tell me:\n"
        "- What topic should the presentation cover?\n"
        "- Any specific URLs or files to include?\n"
        "- Who is the target audience?\n"
        "- How many slides would you like?\n"
        "- What formats do you need? (html, pptx, pdf)"
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
# Agent-powered tools (research, orchestration, editing)
# ---------------------------------------------------------------------------


@mcp.tool()
def research_topic(
    topic: str,
    urls: list[str] | None = None,
    files: list[str] | None = None,
    search_depth: str = "normal",
) -> str:
    """
    Research a topic using web scraping, URL fetching, file reading, and web search.

    Gathers content from provided URLs, local files, and DuckDuckGo search,
    then synthesizes key facts, statistics, quotes, and themes using AI.

    Args:
        topic: The topic to research.
        urls: Optional list of URLs to fetch content from.
        files: Optional list of local file paths (.txt, .md, .pdf, .docx, .pptx).
        search_depth: "quick" (fewer sources), "normal" (default), or "deep" (more sources).

    Returns:
        Structured research summary with key facts, themes, and statistics.
    """
    try:
        orch = _get_orchestrator()
        research = orch.research_only(topic, urls=urls or [], files=files or [])

        # Format for display
        lines = [f"# Research: {topic}\n"]

        if research.get("key_themes"):
            lines.append("## Key Themes")
            for theme in research["key_themes"]:
                lines.append(f"  - {theme}")
            lines.append("")

        if research.get("key_facts"):
            lines.append("## Key Facts")
            for fact in research["key_facts"][:10]:
                importance = fact.get("importance", "medium")
                lines.append(f"  [{importance}] {fact.get('fact', '')}")
            lines.append("")

        if research.get("statistics"):
            lines.append("## Statistics")
            for stat in research["statistics"][:5]:
                lines.append(f"  • {stat.get('stat', '')} — {stat.get('context', '')}")
            lines.append("")

        if research.get("quotes"):
            lines.append("## Notable Quotes")
            for q in research["quotes"][:4]:
                lines.append(f'  > "{q.get("quote", "")}" — {q.get("attribution", "Unknown")}')
            lines.append("")

        if research.get("narrative_arc"):
            lines.append(f"## Suggested Narrative\n{research['narrative_arc']}\n")

        sources = research.get("raw_sources", [])
        lines.append(f"\n*Synthesized from {len(sources)} source(s)*")

        return "\n".join(lines)
    except Exception as e:
        return f"Research failed: {e}"


@mcp.tool()
def create_presentation_from_research(
    topic: str,
    urls: list[str] | None = None,
    files: list[str] | None = None,
    slide_count: int = 10,
    purpose: str = "presentation",
    mood: str = "",
    style_name: str = "",
    audience: str = "",
    output_dir: str = ".",
    output_formats: list[str] | None = None,
    extra_instructions: str = "",
) -> str:
    """
    Create a fully-researched presentation using the AI agent pipeline.

    This runs the complete orchestrated workflow:
    1. Research Agent — gathers content from URLs, web search, and files
    2. Curator Agent — structures research into slides with narrative arc
    3. Style Recommender — picks the best visual theme
    4. Exporters — generates output in requested formats (html, pptx, pdf)

    Args:
        topic: The presentation topic.
        urls: Optional URLs to research from.
        files: Optional local files to include (.txt, .md, .pdf, .docx, .pptx).
        slide_count: Number of slides to create (default 10).
        purpose: Purpose: "pitch", "teaching", "conference", "internal", "presentation".
        mood: Desired audience feeling: "impressed", "excited", "calm", "professional", etc.
        style_name: Specific style preset (leave empty for AI recommendation).
        audience: Target audience description.
        output_dir: Directory for output files.
        output_formats: List of formats: "html", "pptx", "pdf" (default ["html"]).
        extra_instructions: Additional instructions for content generation.

    Returns:
        Session summary with output file paths and edit instructions.
    """
    try:
        orch = _get_orchestrator()
        session = orch.create_presentation(
            topic=topic,
            urls=urls,
            files=files,
            slide_count=slide_count,
            purpose=purpose,
            mood=mood,
            audience=audience,
            style_name=style_name,
            output_dir=output_dir,
            output_formats=output_formats or ["html"],
            extra_instructions=extra_instructions,
        )

        lines = [
            f"# Presentation Created!\n",
            f"**Session ID:** `{session.id}`",
            f"**Title:** {session.presentation_title}",
            f"**Style:** {session.style_name}",
            f"**Slides:** {len(session.slides)}\n",
        ]

        if session.output_paths:
            lines.append("## Output Files")
            for fmt, path in session.output_paths.items():
                if path.startswith("ERROR"):
                    lines.append(f"  ⚠️ {fmt}: {path}")
                else:
                    lines.append(f"  📁 **{fmt.upper()}:** `{path}`")
            lines.append("")

        lines.append("## Slides Overview")
        for i, slide in enumerate(session.slides):
            lines.append(f"  {i+1}. [{slide.get('type', 'content')}] {slide.get('title', 'Untitled')}")

        lines.append(f"\n💡 **To edit:** Use `edit_presentation` with session ID `{session.id}`")
        lines.append(f"💡 **To export:** Use `export_presentation` for additional formats")

        return "\n".join(lines)
    except Exception as e:
        return f"Error creating presentation: {e}"


@mcp.tool()
def edit_presentation(
    session_id: str,
    instruction: str,
) -> str:
    """
    Edit an existing presentation using natural language instructions.

    The Editor Agent interprets your instruction and modifies the slides.
    You can edit content, reorder slides, change types, add/remove slides,
    refine wording, and more.

    Examples:
      "Change slide 3 to a quote slide"
      "Add a new slide about market size after slide 2"
      "Make the bullets on slide 4 more concise"
      "Reorder: put the conclusion before the Q&A"
      "Add speaker notes to all slides"

    Args:
        session_id: The session ID from create_presentation_from_research.
        instruction: Natural language edit instruction.

    Returns:
        Summary of changes made and updated slide list.
    """
    try:
        orch = _get_orchestrator()
        session = orch.edit_presentation(session_id, instruction)

        lines = [
            f"# Presentation Updated\n",
            f"**Session:** `{session.id}`",
            f"**Style:** {session.style_name}",
            f"**Slides:** {len(session.slides)}\n",
        ]

        # Show latest edit
        if session.edit_history:
            latest = session.edit_history[-1]
            lines.append(f"**Edit:** {latest.get('instruction', '')}")
            lines.append(f"**Changes:** {latest.get('summary', '')}\n")

        lines.append("## Updated Slides")
        for i, slide in enumerate(session.slides):
            lines.append(f"  {i+1}. [{slide.get('type', 'content')}] {slide.get('title', 'Untitled')}")

        if session.output_paths:
            lines.append("\n## Regenerated Output")
            for fmt, path in session.output_paths.items():
                if not path.startswith("ERROR"):
                    lines.append(f"  📁 **{fmt.upper()}:** `{path}`")

        return "\n".join(lines)
    except Exception as e:
        return f"Edit failed: {e}"


@mcp.tool()
def export_presentation(
    session_id: str,
    formats: list[str],
    output_dir: str = ".",
) -> str:
    """
    Export an existing presentation session to additional formats.

    Supported formats: "html", "pptx", "pdf"

    Args:
        session_id: The session ID from a previous creation.
        formats: List of output formats (e.g., ["pptx", "pdf"]).
        output_dir: Directory for output files.

    Returns:
        Paths to the generated files.
    """
    try:
        orch = _get_orchestrator()
        output_paths = orch.export_formats(session_id, formats, output_dir)

        lines = [f"# Export Complete\n"]
        for fmt, path in output_paths.items():
            if path.startswith("ERROR"):
                lines.append(f"  ⚠️ **{fmt}:** {path}")
            else:
                lines.append(f"  📁 **{fmt.upper()}:** `{path}`")

        return "\n".join(lines)
    except Exception as e:
        return f"Export failed: {e}"


@mcp.tool()
def apply_pptx_template(
    session_id: str,
    template_path: str,
    output_path: str = "",
) -> str:
    """
    Apply a PPTX template's theme to an existing presentation.

    Extracts colors and fonts from the template file and regenerates
    the presentation with the template's visual identity.

    Args:
        session_id: The session ID to apply the template to.
        template_path: Path to the .pptx template file.
        output_path: Optional output path (defaults to session output dir).

    Returns:
        Path to the regenerated file.
    """
    try:
        orch = _get_orchestrator()
        session = orch.change_style(session_id, pptx_template=template_path)

        lines = [
            f"# Template Applied\n",
            f"**Template:** `{template_path}`",
            f"**Session:** `{session.id}`\n",
        ]

        if session.output_paths:
            for fmt, path in session.output_paths.items():
                if not path.startswith("ERROR"):
                    lines.append(f"  📁 **{fmt.upper()}:** `{path}`")

        return "\n".join(lines)
    except Exception as e:
        return f"Template application failed: {e}"


@mcp.tool()
def list_sessions() -> str:
    """
    List all saved presentation sessions.

    Returns session IDs, topics, and last updated timestamps.
    Use these IDs with edit_presentation or export_presentation.
    """
    try:
        orch = _get_orchestrator()
        sessions = orch.list_sessions()

        if not sessions:
            return "No saved sessions found. Create one with `create_presentation_from_research`."

        lines = ["# Saved Sessions\n"]
        for s in sessions:
            lines.append(
                f"  `{s['id']}` — **{s.get('topic', 'Untitled')}** "
                f"({s.get('slides', '0')} slides, style: {s.get('style', 'N/A')}) "
                f"— {s.get('updated', '')}"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing sessions: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

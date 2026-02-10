"""
Slide Builder MCP — HTML Presentation Generator.

Generates self-contained HTML presentations from structured content
using Jinja2 templates and style presets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, BaseLoader

from .styles import load_preset, presets_for_mood

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _read_template(name: str) -> str:
    """Read a template file from the templates directory."""
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _build_font_import(preset: dict[str, Any]) -> str:
    """Build the font import URL from preset config."""
    return preset.get("font_import", "")


def _build_color_swatches(preset: dict[str, Any]) -> str:
    """Build HTML for color palette swatches in preview."""
    colors = preset.get("colors", {})
    swatches = []
    for key, value in colors.items():
        if not value.startswith("linear-gradient") and not value.startswith("rgba"):
            swatches.append(f'<div class="swatch" style="background: {value};" title="{key}"></div>')
    return "\n        ".join(swatches)


def _build_slide_html(slides: list[dict[str, Any]], preset: dict[str, Any]) -> str:
    """
    Build the HTML for all slides from structured content.

    Each slide dict should have:
      - type: "title" | "content" | "feature_grid" | "code" | "quote" | "image" | "closing"
      - title: str (heading)
      - subtitle: str (optional)
      - bullets: list[str] (optional)
      - code: str (optional, for code slides)
      - quote: str (optional, for quote slides)
      - attribution: str (optional, for quote slides)
      - cards: list[dict] (optional, for feature_grid slides)
      - image_src: str (optional, for image slides)
    """
    parts: list[str] = []

    for i, slide in enumerate(slides):
        slide_type = slide.get("type", "content")
        title = slide.get("title", "")
        subtitle = slide.get("subtitle", "")
        bullets = slide.get("bullets", [])
        code = slide.get("code", "")
        quote = slide.get("quote", "")
        attribution = slide.get("attribution", "")
        cards = slide.get("cards", [])
        image_src = slide.get("image_src", "")

        css_class = f"slide {slide_type}-slide"

        if slide_type == "title":
            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <h1 class="reveal">{title}</h1>
            {f'<p class="reveal subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
    </section>""")

        elif slide_type == "quote":
            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <blockquote class="reveal" style="font-family: var(--font-display); font-size: var(--h2-size); font-style: italic; max-width: 800px;">
                &ldquo;{quote}&rdquo;
            </blockquote>
            {f'<p class="reveal" style="margin-top: 1rem; color: var(--text-secondary);">— {attribution}</p>' if attribution else ''}
        </div>
    </section>""")

        elif slide_type == "code":
            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content">
            <h2 class="reveal">{title}</h2>
            <pre class="reveal" style="background: rgba(0,0,0,0.3); padding: clamp(1rem, 2vw, 2rem); border-radius: 8px; overflow: hidden; font-family: 'JetBrains Mono', monospace; font-size: var(--small-size); line-height: 1.6; margin-top: var(--content-gap);"><code>{code}</code></pre>
        </div>
    </section>""")

        elif slide_type == "feature_grid":
            cards_html = ""
            for card in cards[:6]:  # Max 6 cards
                card_title = card.get("title", "")
                card_desc = card.get("description", "")
                card_icon = card.get("icon", "")
                cards_html += f"""
                <div class="card reveal" style="background: rgba(255,255,255,0.05); padding: clamp(1rem, 2vw, 1.5rem); border-radius: 12px;">
                    {f'<div style="font-size: 1.5em; margin-bottom: 0.5rem;">{card_icon}</div>' if card_icon else ''}
                    <h3 style="font-size: var(--body-size); font-weight: 600; margin-bottom: 0.5rem;">{card_title}</h3>
                    <p style="font-size: var(--small-size); color: var(--text-secondary);">{card_desc}</p>
                </div>"""

            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content">
            <h2 class="reveal">{title}</h2>
            <div class="grid" style="margin-top: var(--content-gap);">
                {cards_html}
            </div>
        </div>
    </section>""")

        elif slide_type == "image":
            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content" style="align-items: center;">
            <h2 class="reveal">{title}</h2>
            <img class="reveal" src="{image_src}" alt="{title}" style="margin-top: var(--content-gap); border-radius: 8px;">
        </div>
    </section>""")

        elif slide_type == "closing":
            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content" style="align-items: center; text-align: center;">
            <h1 class="reveal">{title}</h1>
            {f'<p class="reveal subtitle" style="margin-top: var(--content-gap);">{subtitle}</p>' if subtitle else ''}
        </div>
    </section>""")

        else:
            # Default content slide
            bullets_html = ""
            if bullets:
                items = "\n                ".join(
                    f'<li class="reveal">{b}</li>' for b in bullets[:6]
                )
                bullets_html = f"""
            <ul class="bullet-list" style="margin-top: var(--content-gap); list-style: none; padding: 0; display: flex; flex-direction: column; gap: var(--element-gap);">
                {items}
            </ul>"""

            subtitle_html = ""
            if subtitle and not bullets:
                subtitle_html = f'<p class="reveal" style="margin-top: var(--content-gap); color: var(--text-secondary);">{subtitle}</p>'

            parts.append(f"""
    <section class="{css_class}">
        <div class="slide-content">
            <h2 class="reveal">{title}</h2>
            {subtitle_html}
            {bullets_html}
        </div>
    </section>""")

    return "\n".join(parts)


def generate_presentation(
    title: str,
    slides: list[dict[str, Any]],
    style_name: str,
    output_path: str,
) -> str:
    """
    Generate a complete HTML presentation file.

    Args:
        title: Presentation title (used in <title>).
        slides: List of slide dicts (see _build_slide_html for schema).
        style_name: Preset name to use.
        output_path: Where to write the HTML file.

    Returns:
        Absolute path to the generated file.
    """
    preset = load_preset(style_name)
    template_str = _read_template("base.html")

    # Build template variables
    variables = {
        "title": title,
        "font_import": _build_font_import(preset),
        "colors": preset["colors"],
        "fonts": preset["fonts"],
        "extra_css": preset.get("extra_css", ""),
        "slides_html": _build_slide_html(slides, preset),
    }

    # Simple Jinja2-style replacement using string format
    # We do manual replacement since our template uses {{ }} syntax
    env = Environment(loader=BaseLoader())
    # Replace nested dotted access with flat vars
    flat_vars: dict[str, str] = {}
    flat_vars["title"] = title
    flat_vars["font_import"] = variables["font_import"]
    flat_vars["extra_css"] = variables["extra_css"]
    flat_vars["slides_html"] = variables["slides_html"]

    colors = preset["colors"]
    for k, v in colors.items():
        flat_vars[f"colors.{k}"] = v

    fonts = preset["fonts"]
    flat_vars["fonts.display.family"] = fonts["display"]["family"]
    flat_vars["fonts.body.family"] = fonts["body"]["family"]

    # Manual template rendering (safe for our controlled templates)
    rendered = template_str
    for key, value in flat_vars.items():
        rendered = rendered.replace("{{ " + key + " }}", str(value))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    return str(out.resolve())


def generate_preview(
    style_name: str,
    output_path: str,
    preview_title: str = "Your Presentation Title",
    preview_subtitle: str = "A beautiful slide deck crafted just for you",
) -> str:
    """
    Generate a single-slide style preview HTML file.

    Args:
        style_name: Preset name.
        output_path: Where to write the preview HTML.
        preview_title: Title text for preview.
        preview_subtitle: Subtitle text for preview.

    Returns:
        Absolute path to the preview file.
    """
    preset = load_preset(style_name)
    template_str = _read_template("preview.html")

    flat_vars: dict[str, str] = {
        "preset_name": preset["display_name"],
        "font_import": _build_font_import(preset),
        "extra_css": preset.get("extra_css", ""),
        "preview_title": preview_title,
        "preview_subtitle": preview_subtitle,
        "color_swatches": _build_color_swatches(preset),
    }

    colors = preset["colors"]
    for k, v in colors.items():
        flat_vars[f"colors.{k}"] = v

    fonts = preset["fonts"]
    flat_vars["fonts.display.family"] = fonts["display"]["family"]
    flat_vars["fonts.body.family"] = fonts["body"]["family"]

    rendered = template_str
    for key, value in flat_vars.items():
        rendered = rendered.replace("{{ " + key + " }}", str(value))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    return str(out.resolve())


def generate_mood_previews(
    mood: str,
    output_dir: str,
    preview_title: str = "Your Presentation Title",
    preview_subtitle: str = "A beautiful slide deck crafted just for you",
) -> list[dict[str, str]]:
    """
    Generate 3 style preview files based on a mood keyword.

    Args:
        mood: Mood keyword (e.g., "excited", "professional").
        output_dir: Directory for preview files.
        preview_title: Preview title text.
        preview_subtitle: Preview subtitle text.

    Returns:
        List of dicts with name, display_name, path, and vibe.
    """
    preset_names = presets_for_mood(mood)
    results = []

    for i, name in enumerate(preset_names[:3]):
        preset = load_preset(name)
        suffix = chr(ord("a") + i)  # a, b, c
        out_path = str(Path(output_dir) / f"style-{suffix}.html")
        generate_preview(name, out_path, preview_title, preview_subtitle)
        results.append({
            "name": name,
            "display_name": preset["display_name"],
            "path": out_path,
            "vibe": preset["vibe"],
        })

    return results

"""
HTML Exporter — wraps the existing generator for consistency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_html(
    title: str,
    slides: list[dict[str, Any]],
    style_name: str,
    output_path: str,
    custom_preset: dict[str, Any] | None = None,
) -> str:
    """
    Generate HTML presentation using the existing generator.

    If a custom_preset is provided, it's written to a temp location
    and used instead of a named preset.
    """
    if custom_preset:
        return _export_with_custom_preset(title, slides, custom_preset, output_path)

    from ..generator import generate_presentation
    return generate_presentation(title, slides, style_name, output_path)


def _export_with_custom_preset(
    title: str,
    slides: list[dict[str, Any]],
    preset: dict[str, Any],
    output_path: str,
) -> str:
    """Generate HTML using a custom preset dict (not from a file)."""
    from ..generator import _read_template, _build_slide_html, _build_font_import

    template_str = _read_template("base.html")

    flat_vars: dict[str, str] = {}
    flat_vars["title"] = title
    flat_vars["font_import"] = _build_font_import(preset)
    flat_vars["extra_css"] = preset.get("extra_css", "")
    flat_vars["slides_html"] = _build_slide_html(slides)

    colors = preset.get("colors", {})
    for k, v in colors.items():
        flat_vars[f"colors.{k}"] = v

    fonts = preset.get("fonts", {})
    flat_vars["fonts.display.family"] = fonts.get("display", {}).get("family", "Inter")
    flat_vars["fonts.body.family"] = fonts.get("body", {}).get("family", "Inter")

    rendered = template_str
    for key, value in flat_vars.items():
        rendered = rendered.replace("{{ " + key + " }}", str(value))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    return str(out.resolve())

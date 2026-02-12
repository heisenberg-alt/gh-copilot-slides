"""
Exporters — output slide presentations in multiple formats.

Supports: HTML, PPTX, PDF
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .html_exporter import export_html
from .pptx_exporter import export_pptx
from .pdf_exporter import export_pdf

logger = logging.getLogger("slide-builder.exporters")

__all__ = ["export_html", "export_pptx", "export_pdf", "export_all"]

EXPORTERS = {
    "html": export_html,
    "pptx": export_pptx,
    "pdf": export_pdf,
}


def export_all(
    title: str,
    slides: list[dict[str, Any]],
    style_name: str,
    output_dir: str = ".",
    formats: list[str] | None = None,
    custom_preset: dict[str, Any] | None = None,
    pptx_template: str | None = None,
) -> dict[str, str]:
    """
    Export a presentation to all requested formats.

    Returns a dict mapping format → output file path.
    """
    formats = formats or ["html"]
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Generate a safe base filename from title
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe_name = safe_name.strip().replace(" ", "-").lower()[:50] or "presentation"

    results: dict[str, str] = {}

    for fmt in formats:
        fmt = fmt.lower().strip()
        if fmt not in EXPORTERS:
            logger.warning(f"Unknown format: {fmt}")
            continue

        output_path = str(output_dir_path / f"{safe_name}.{fmt}")

        try:
            if fmt == "html":
                result = export_html(
                    title=title,
                    slides=slides,
                    style_name=style_name,
                    output_path=output_path,
                    custom_preset=custom_preset,
                )
            elif fmt == "pptx":
                result = export_pptx(
                    title=title,
                    slides=slides,
                    style_name=style_name,
                    output_path=output_path,
                    custom_preset=custom_preset,
                    template_path=pptx_template,
                )
            elif fmt == "pdf":
                # PDF is generated from the HTML output
                html_path = results.get("html")
                if not html_path:
                    # Generate HTML first if not already done
                    html_path = str(output_dir_path / f"{safe_name}.html")
                    export_html(
                        title=title,
                        slides=slides,
                        style_name=style_name,
                        output_path=html_path,
                        custom_preset=custom_preset,
                    )
                result = export_pdf(
                    html_path=html_path,
                    output_path=output_path,
                )
            else:
                continue

            results[fmt] = result
            logger.info(f"Exported {fmt}: {result}")
        except Exception as e:
            logger.error(f"Export failed for {fmt}: {e}")
            results[fmt] = f"ERROR: {e}"

    return results

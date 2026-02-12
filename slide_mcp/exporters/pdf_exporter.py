"""
PDF Exporter — converts HTML presentations to PDF using Playwright.

Uses headless Chromium to render the HTML presentation and capture
each slide as a PDF page, preserving full CSS styling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("slide-builder.exporters.pdf")


def export_pdf(
    html_path: str,
    output_path: str,
    width: str = "13.333in",
    height: str = "7.5in",
) -> str:
    """
    Generate a PDF from an HTML presentation using Playwright.

    The HTML file is loaded in headless Chromium and rendered to PDF
    with 16:9 landscape pages matching the slide dimensions.

    Args:
        html_path: Path to the HTML presentation file.
        output_path: Where to write the PDF.
        width: Page width (default 16:9 landscape).
        height: Page height (default 16:9 landscape).

    Returns:
        Absolute path to the generated PDF.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError(
            "Playwright is required for PDF export.\n"
            "Install with: pip install playwright && python -m playwright install chromium"
        )

    html_file = Path(html_path).resolve()
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    file_url = f"file://{html_file}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the HTML file
        page.goto(file_url, wait_until="networkidle")

        # Wait for fonts and animations to load
        page.wait_for_timeout(2000)

        # Get the number of slides by counting <section class="slide"> elements
        slide_count = page.evaluate(
            "document.querySelectorAll('section.slide, .slide').length"
        )

        if slide_count == 0:
            # Fallback: just print the whole page
            page.pdf(
                path=str(out),
                width=width,
                height=height,
                print_background=True,
                prefer_css_page_size=False,
                landscape=True,
            )
        else:
            # Inject print styles to render one slide per page
            page.evaluate("""() => {
                // Remove scroll-snap and fixed positioning for print
                const style = document.createElement('style');
                style.textContent = `
                    @media print {
                        * { animation: none !important; transition: none !important; }
                        body { overflow: visible !important; height: auto !important; scroll-snap-type: none !important; }
                        section.slide, .slide {
                            page-break-after: always;
                            page-break-inside: avoid;
                            height: 100vh;
                            min-height: 100vh;
                            scroll-snap-align: none;
                            position: relative !important;
                        }
                        section.slide:last-child, .slide:last-child {
                            page-break-after: auto;
                        }
                        .reveal, .reveal-scale, .reveal-blur {
                            opacity: 1 !important;
                            transform: none !important;
                            filter: none !important;
                        }
                        .reveal.visible { opacity: 1 !important; }
                        .progress-bar, .nav-dots { display: none !important; }
                    }
                `;
                document.head.appendChild(style);

                // Make all reveals visible
                document.querySelectorAll('.reveal, .reveal-scale, .reveal-blur').forEach(el => {
                    el.classList.add('visible');
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                    el.style.filter = 'none';
                });
            }""")

            page.pdf(
                path=str(out),
                width=width,
                height=height,
                print_background=True,
                prefer_css_page_size=False,
                landscape=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )

        browser.close()

    logger.info(f"PDF exported: {out.resolve()}")
    return str(out.resolve())

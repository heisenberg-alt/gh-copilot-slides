"""
Style preset endpoints.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Path to presets directory
PRESETS_DIR = Path(__file__).parent.parent.parent.parent.parent / "templates" / "presets"

# Valid style name pattern (alphanumeric, underscore, hyphen only)
VALID_STYLE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")


class StylePreset(BaseModel):
    """Style preset information."""

    name: str
    display_name: str
    description: str
    category: str  # "dark", "light", "specialty"
    colors: dict
    fonts: dict
    preview_url: Optional[str] = None


class StylesResponse(BaseModel):
    """Response containing all available styles."""

    styles: list[StylePreset]


def determine_category(name: str, bg_color: str) -> str:
    """
    Determine the style category based on name patterns and background color.

    Args:
        name: The style preset name
        bg_color: The background color hex value

    Returns:
        Category string: "dark" or "light"
    """
    dark_keywords = ("dark", "neon", "terminal", "cyber")
    light_keywords = ("pastel", "notebook", "vintage", "light")
    dark_backgrounds = ("#000", "#000000", "#1c1c1e", "#0a0a0a", "#0f0f0f")

    name_lower = name.lower()

    if any(keyword in name_lower for keyword in dark_keywords):
        return "dark"
    if any(keyword in name_lower for keyword in light_keywords):
        return "light"

    # Check background brightness
    return "dark" if bg_color.lower() in dark_backgrounds else "light"


def load_style_preset(preset_file: Path) -> Optional[StylePreset]:
    """
    Load a style preset from a JSON file.

    Args:
        preset_file: Path to the preset JSON file

    Returns:
        StylePreset object or None if loading fails
    """
    try:
        with open(preset_file) as f:
            data = json.load(f)

        name = preset_file.stem
        bg_color = data.get("colors", {}).get("background", "#ffffff")
        category = determine_category(name, bg_color)

        return StylePreset(
            name=name,
            display_name=data.get("name", name.replace("_", " ").title()),
            description=data.get("description", ""),
            category=category,
            colors=data.get("colors", {}),
            fonts=data.get("fonts", {}),
        )
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load style preset %s: %s", preset_file, e)
        return None


@router.get("", response_model=StylesResponse)
async def list_styles():
    """
    List all available style presets.

    Returns preset metadata including colors and fonts for preview.
    """
    styles: list[StylePreset] = []

    if PRESETS_DIR.exists():
        for preset_file in PRESETS_DIR.glob("*.json"):
            style = load_style_preset(preset_file)
            if style:
                styles.append(style)

    # Sort by category then name
    styles.sort(key=lambda s: (s.category, s.name))

    return StylesResponse(styles=styles)


@router.get("/{style_name}", response_model=StylePreset)
async def get_style(style_name: str):
    """Get details for a specific style preset."""
    # Validate style name to prevent path traversal
    if not VALID_STYLE_NAME.match(style_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid style name. Use only letters, numbers, underscores, and hyphens."
        )

    preset_file = PRESETS_DIR / f"{style_name}.json"

    # Additional safety check - ensure resolved path is within PRESETS_DIR
    try:
        preset_file.resolve().relative_to(PRESETS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid style name")

    if not preset_file.exists():
        raise HTTPException(status_code=404, detail="Style not found")

    style = load_style_preset(preset_file)
    if not style:
        raise HTTPException(status_code=500, detail="Failed to load style")

    return style

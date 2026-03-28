"""Theme-based product image generation service.

Uses Gemini's image generation capabilities to create product images
with themed backgrounds and styling appropriate for e-commerce display.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ceramicraft_product_agent.templates.categorization import CATEGORIES
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Theme definitions for product photography
# ---------------------------------------------------------------------------

THEMES: dict[str, dict[str, str]] = {
    "minimalist": {
        "background": "clean white studio background with soft shadows",
        "lighting": "bright, even studio lighting with gentle highlights",
        "props": "none, pure product focus",
        "mood": "clean, modern, professional",
    },
    "rustic_table": {
        "background": "warm wooden table with linen cloth",
        "lighting": "warm natural window light from the side",
        "props": "dried flowers, wooden utensils, natural textures",
        "mood": "cozy, inviting, artisanal",
    },
    "garden_scene": {
        "background": "lush green garden with soft bokeh",
        "lighting": "golden hour sunlight filtering through leaves",
        "props": "fresh flowers, moss, garden elements",
        "mood": "natural, fresh, organic",
    },
    "luxury_display": {
        "background": "dark marble surface with velvet fabric",
        "lighting": "dramatic spotlight with deep shadows",
        "props": "gold accents, silk fabric, elegant arrangement",
        "mood": "premium, exclusive, sophisticated",
    },
    "kitchen_lifestyle": {
        "background": "bright modern kitchen counter",
        "lighting": "bright overhead with warm fill light",
        "props": "fresh ingredients, herbs, cooking elements",
        "mood": "practical, lifestyle, everyday elegance",
    },
    "seasonal_holiday": {
        "background": "festive setting with seasonal decorations",
        "lighting": "warm ambient glow with candle-like accents",
        "props": "seasonal flowers, ribbons, festive elements",
        "mood": "celebratory, warm, gift-worthy",
    },
}

# ---------------------------------------------------------------------------
# Image generation prompt template
# ---------------------------------------------------------------------------

IMAGE_PROMPT_TEMPLATE = """\
Generate a professional e-commerce product photograph of a {product_type}.

Product: {name}
Material: {material}
Style: {style}
Color/Glaze: {color}

Photography Setting:
- Background: {background}
- Lighting: {lighting}
- Props: {props}
- Mood: {mood}

Photography Requirements:
- High-resolution product photography style
- Product should be the clear focal point
- {angle} camera angle
- Sharp focus on the product with appropriate depth of field
- Color-accurate representation of the ceramic piece
- Professional e-commerce quality suitable for online marketplace
"""


def select_theme(product: dict[str, Any]) -> str:
    """Select the best image theme based on product attributes."""
    category = product.get("category", "")
    style = product.get("style", "")

    # Theme selection logic based on product characteristics
    if category in ("garden_outdoor",):
        return "garden_scene"
    if style in ("luxury",):
        return "luxury_display"
    if style in ("rustic",):
        return "rustic_table"
    if category in ("kitchenware", "dinnerware"):
        return "kitchen_lifestyle"
    if category in ("tea_sets",):
        return "rustic_table"

    return "minimalist"


def build_image_prompt(product: dict[str, Any], theme: str | None = None) -> str:
    """Build the image generation prompt for Gemini.

    Args:
        product: Product attributes dict.
        theme: Optional theme override. Auto-selected if not provided.

    Returns:
        Formatted prompt string for image generation.
    """
    if theme is None:
        theme = select_theme(product)

    theme_config = THEMES.get(theme, THEMES["minimalist"])
    cat_display = CATEGORIES.get(
        product.get("category", ""), {}
    ).get("display_name", product.get("category", "ceramic piece"))

    # Select camera angle based on product type
    angle_map = {
        "dinnerware": "45-degree overhead",
        "drinkware": "eye-level front",
        "vases_decor": "slightly low angle",
        "tea_sets": "45-degree overhead",
        "kitchenware": "eye-level front",
        "tiles_panels": "straight-on front",
        "garden_outdoor": "eye-level front",
    }
    angle = angle_map.get(product.get("category", ""), "45-degree")

    return IMAGE_PROMPT_TEMPLATE.format(
        product_type=cat_display,
        name=product.get("name", "Ceramic Product"),
        material=product.get("material", "ceramic"),
        style=product.get("style", "classic"),
        color=product.get("color", product.get("attributes", {}).get("color", "natural glaze")),
        background=theme_config["background"],
        lighting=theme_config["lighting"],
        props=theme_config["props"],
        mood=theme_config["mood"],
        angle=angle,
    )


@tool
def generate_image_prompt_tool(product: dict[str, Any]) -> dict[str, Any]:
    """Generate a themed image prompt for a ceramic product.

    Returns the image generation prompt and selected theme metadata.
    """
    theme = select_theme(product)
    prompt = build_image_prompt(product, theme)

    return {
        "image_prompt": prompt,
        "theme": theme,
        "theme_config": THEMES[theme],
    }

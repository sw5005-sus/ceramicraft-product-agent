"""Product description generation service.

Generates SEO-friendly product descriptions using Gemini LLM with
fixed templates, falling back to template-based generation when the
API is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from ceramicraft_product_agent.templates.categorization import CATEGORIES
from ceramicraft_product_agent.templates.description import (
    FALLBACK_DESCRIPTION,
    SEO_KEYWORDS_PROMPT,
    DESCRIPTION_PROMPT,
)
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)


def build_seo_keywords_prompt(product: dict[str, Any]) -> str:
    """Build the prompt for SEO keyword generation."""
    return SEO_KEYWORDS_PROMPT.format(
        name=product.get("name", "Unknown"),
        category=product.get("category", "ceramics"),
        style=product.get("style", "traditional"),
        material=product.get("material", "ceramic"),
    )


def parse_seo_keywords_response(response_text: str) -> list[str]:
    """Parse the JSON array of SEO keywords from LLM response."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        keywords = json.loads(cleaned)
        if isinstance(keywords, list):
            return [str(kw) for kw in keywords[:8]]
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse SEO keywords: %s", exc)

    return _default_seo_keywords(product={})


def _default_seo_keywords(product: dict[str, Any]) -> list[str]:
    """Generate default SEO keywords from product attributes."""
    name = product.get("name", "ceramic")
    category = product.get("category", "ceramics")
    style = product.get("style", "handmade")
    material = product.get("material", "ceramic")

    cat_display = CATEGORIES.get(category, {}).get("display_name", category)
    return [
        name.lower(),
        f"{material} {cat_display}".lower(),
        f"{style} ceramics",
        "handcrafted ceramic",
        "premium pottery",
        f"{material} craft",
        "ceramicraft",
        "artisan ceramic",
    ]


def build_description_prompt(product: dict[str, Any], seo_keywords: list[str]) -> str:
    """Build the Gemini prompt for description generation."""
    return DESCRIPTION_PROMPT.format(
        name=product.get("name", "Unknown"),
        category=CATEGORIES.get(
            product.get("category", ""), {}
        ).get("display_name", product.get("category", "Ceramic")),
        style=product.get("style", "traditional"),
        material=product.get("material", "ceramic"),
        dimensions=product.get("dimensions", "Not specified"),
        tags=", ".join(product.get("tags", [])),
        attributes=json.dumps(product.get("attributes", {})),
        seo_keywords=", ".join(seo_keywords),
    )


def build_fallback_description(product: dict[str, Any]) -> str:
    """Generate a template-based description when Gemini is unavailable."""
    cat_display = CATEGORIES.get(
        product.get("category", ""), {}
    ).get("display_name", product.get("category", "ceramic"))

    return FALLBACK_DESCRIPTION.format(
        name=product.get("name", "Ceramic Piece"),
        category=cat_display,
        style=product.get("style", "classic"),
        material=product.get("material", "ceramic"),
        dimensions=product.get("dimensions", "standard size"),
    )


@tool
def generate_description_tool(product: dict[str, Any]) -> dict[str, Any]:
    """Generate an SEO-friendly product description.

    Returns description text and SEO keywords.
    """
    seo_keywords = _default_seo_keywords(product)
    description = build_fallback_description(product)
    return {
        "description": description,
        "seo_keywords": seo_keywords,
    }

"""Promotional text generation service.

Generates targeted promotional content using Gemini LLM with fixed
templates, falling back to template-based generation when the API
is unavailable.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from ceramicraft_product_agent.templates.categorization import CATEGORIES
from ceramicraft_product_agent.templates.promotion import (
    FALLBACK_PROMOTION,
    PROMOTION_PROMPT,
    PROMOTION_TYPES,
)
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)


def build_promotion_prompt(product: dict[str, Any], promotion_type: str) -> str:
    """Build the Gemini prompt for promotional text generation."""
    ptype_desc = PROMOTION_TYPES.get(promotion_type, PROMOTION_TYPES["new_arrival"])

    return PROMOTION_PROMPT.format(
        name=product.get("name", "Unknown"),
        category=CATEGORIES.get(product.get("category", ""), {}).get(
            "display_name", product.get("category", "Ceramic")
        ),
        style=product.get("style", "traditional"),
        material=product.get("material", "ceramic"),
        price=product.get("price", "N/A"),
        tags=", ".join(product.get("tags", [])),
        promotion_type=ptype_desc,
    )


def parse_promotion_response(response_text: str) -> dict[str, Any]:
    """Parse the JSON promotion response from LLM."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        result = json.loads(cleaned)
        return {
            "headline": str(result.get("headline", ""))[:60],
            "short_text": str(result.get("short_text", ""))[:150],
            "long_text": str(result.get("long_text", "")),
            "call_to_action": str(result.get("call_to_action", "Shop Now"))[:30],
            "hashtags": [str(h) for h in result.get("hashtags", [])][:5],
        }
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse LLM promotion response: %s", exc)
        return build_fallback_promotion({})


def build_fallback_promotion(product: dict[str, Any]) -> dict[str, Any]:
    """Generate template-based promotional content when Gemini is unavailable."""
    cat_display = CATEGORIES.get(product.get("category", ""), {}).get(
        "display_name", product.get("category", "ceramics")
    )

    fmt_kwargs = {
        "name": product.get("name", "Ceramic Piece"),
        "category": cat_display,
        "style": product.get("style", "classic"),
        "material": product.get("material", "ceramic"),
    }

    return {
        "headline": FALLBACK_PROMOTION["headline"].format(**fmt_kwargs),
        "short_text": FALLBACK_PROMOTION["short_text"].format(**fmt_kwargs),
        "long_text": FALLBACK_PROMOTION["long_text"].format(**fmt_kwargs),
        "call_to_action": FALLBACK_PROMOTION["call_to_action"],
        "hashtags": [h.format(**fmt_kwargs) for h in FALLBACK_PROMOTION["hashtags"]],
    }


@tool
def generate_promotion_tool(
    product: dict[str, Any], promotion_type: str = "new_arrival"
) -> dict[str, Any]:
    """Generate promotional text for a product.

    Returns headline, short_text, long_text, call_to_action, and hashtags.
    """
    return build_fallback_promotion(product)

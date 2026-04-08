"""Auto-categorization engine for ceramic products.

Combines keyword-based heuristics with Gemini LLM for accurate product
classification into categories and styles.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from ceramicraft_product_agent.templates.categorization import (
    CATEGORIES,
    CATEGORIZATION_PROMPT,
    STYLES,
)
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)


def _keyword_match_score(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in the given text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def classify_by_rules(product: dict[str, Any]) -> dict[str, Any]:
    """Classify a product using keyword-matching heuristics.

    Returns a dict with category, style, tags, and confidence.
    """
    searchable = " ".join([
        product.get("name", ""),
        product.get("material", ""),
        product.get("desc", product.get("description_hints", "")),
        product.get("capacity", ""),
        product.get("care_instructions", ""),
        " ".join(product.get("attributes", {}).values())
        if isinstance(product.get("attributes"), dict)
        else str(product.get("attributes", "")),
    ]).lower()

    # Score each category
    category_scores: dict[str, int] = {}
    for cat_key, cat_info in CATEGORIES.items():
        score = _keyword_match_score(searchable, cat_info["keywords"])
        # Bonus for matching material
        material = product.get("material", "").lower()
        if material in [m.lower() for m in cat_info["materials"]]:
            score += 2
        category_scores[cat_key] = score

    best_category = max(category_scores, key=category_scores.get)  # type: ignore[arg-type]
    best_cat_score = category_scores[best_category]

    # Score each style
    style_scores: dict[str, int] = {}
    for style_key, style_keywords in STYLES.items():
        style_scores[style_key] = _keyword_match_score(searchable, style_keywords)

    best_style = max(style_scores, key=style_scores.get)  # type: ignore[arg-type]

    # Generate tags from matched keywords
    tags: list[str] = []
    cat_info = CATEGORIES[best_category]
    for kw in cat_info["keywords"]:
        if kw in searchable and kw not in tags:
            tags.append(kw)
    if len(tags) < 3:
        tags.extend([product.get("material", "ceramic"), best_style])

    # Confidence based on score magnitude
    confidence = min(best_cat_score / 5.0, 1.0) if best_cat_score > 0 else 0.2

    return {
        "category": best_category,
        "style": best_style,
        "tags": tags[:8],
        "confidence": round(confidence, 2),
    }


def build_categorization_prompt(product: dict[str, Any]) -> str:
    """Build the Gemini prompt for LLM-assisted categorization."""
    return CATEGORIZATION_PROMPT.format(
        name=product.get("name", "Unknown"),
        material=product.get("material", "Unknown"),
        description_hints=product.get("desc", product.get("description_hints", "None")),
        dimensions=product.get("dimensions", "Not specified"),
        attributes=json.dumps(product.get("attributes", {})),
        categories=", ".join(CATEGORIES.keys()),
        styles=", ".join(STYLES.keys()),
    )


def parse_categorization_response(response_text: str) -> dict[str, Any]:
    """Parse the JSON response from the Gemini categorization call."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        result = json.loads(cleaned)

        # Validate category and style
        if result.get("category") not in CATEGORIES:
            result["category"] = "vases_decor"
        if result.get("style") not in STYLES:
            result["style"] = "traditional"

        return {
            "category": result["category"],
            "style": result["style"],
            "tags": result.get("tags", [])[:8],
            "confidence": min(max(float(result.get("confidence", 0.5)), 0.0), 1.0),
        }
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse LLM categorization response: %s", exc)
        return {"category": "vases_decor", "style": "traditional", "tags": [], "confidence": 0.3}


@tool
def categorize_product_tool(product: dict[str, Any]) -> dict[str, Any]:
    """Categorize a ceramic product based on its attributes.

    Returns category, style, tags, and confidence score.
    """
    return classify_by_rules(product)

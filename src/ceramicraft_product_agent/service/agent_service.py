"""Agent service.

Orchestrates the full product-processing pipeline using LangGraph:
  categorization → description generation → promotion generation → image prompt.

The LangGraph StateGraph defines each processing step as a node and wires them
into a deterministic sequential workflow. A Google Gemini LLM powers the
content generation, with rule-based fallbacks for offline operation.

This is the single entry point used by the API layer.
"""

from __future__ import annotations

import json
import os
from typing import Any, cast

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from ceramicraft_product_agent.service.categorization import (
    build_categorization_prompt,
    categorize_product_tool,
    classify_by_rules,
    parse_categorization_response,
)
from ceramicraft_product_agent.service.description_gen import (
    build_description_prompt,
    build_fallback_description,
    build_seo_keywords_prompt,
    parse_seo_keywords_response,
)
from ceramicraft_product_agent.service.image_gen import (
    build_image_prompt,
    generate_image_prompt_tool,
    select_theme,
)
from ceramicraft_product_agent.service.promotion_gen import (
    build_fallback_promotion,
    build_promotion_prompt,
    generate_promotion_tool,
    parse_promotion_response,
)
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# LangGraph state definition
# ---------------------------------------------------------------------------


class _ProductState(TypedDict):
    """Mutable state passed between LangGraph nodes."""

    product: dict[str, Any]
    promotion_type: str
    categorization: dict[str, Any]
    description: dict[str, Any]
    promotion: dict[str, Any]
    image: dict[str, Any]


# ---------------------------------------------------------------------------
# Gemini LLM singleton
# ---------------------------------------------------------------------------

_llm: ChatGoogleGenerativeAI | None = None


def _get_llm() -> ChatGoogleGenerativeAI | None:
    """Return a module-level Gemini LLM singleton (created on first use).

    Returns None if GOOGLE_API_KEY is not set.
    """
    global _llm
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key,
        )
    return _llm


def _invoke_llm(prompt: str) -> str | None:
    """Invoke the Gemini LLM with a prompt. Returns None on failure."""
    llm = _get_llm()
    if llm is None:
        return None
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)
    except Exception as exc:
        logger.warning("Gemini API call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# LangGraph node functions
# ---------------------------------------------------------------------------


def _categorize_node(state: _ProductState) -> dict[str, Any]:
    """Node: classify the product into category and style."""
    product = state["product"]
    logger.info("Categorizing product: %s", product.get("name", "unknown"))

    # Try LLM-assisted categorization first
    prompt = build_categorization_prompt(product)
    response = _invoke_llm(prompt)

    if response is not None:
        categorization = parse_categorization_response(response)
        logger.info(
            "LLM categorization: category=%s style=%s confidence=%.2f",
            categorization["category"],
            categorization["style"],
            categorization["confidence"],
        )
    else:
        logger.warning("GOOGLE_API_KEY not set or LLM failed – using rule-based categorization.")
        categorization = classify_by_rules(product)

    return {"categorization": categorization}


def _generate_description_node(state: _ProductState) -> dict[str, Any]:
    """Node: generate SEO-friendly product description."""
    product = {**state["product"], **state["categorization"]}
    logger.info("Generating description for: %s", product.get("name", "unknown"))

    # Generate SEO keywords first
    seo_prompt = build_seo_keywords_prompt(product)
    seo_response = _invoke_llm(seo_prompt)
    if seo_response is not None:
        seo_keywords = parse_seo_keywords_response(seo_response)
    else:
        from ceramicraft_product_agent.service.description_gen import _default_seo_keywords
        seo_keywords = _default_seo_keywords(product)

    # Generate description
    desc_prompt = build_description_prompt(product, seo_keywords)
    desc_response = _invoke_llm(desc_prompt)
    if desc_response is not None:
        description = desc_response.strip()
    else:
        logger.warning("Using fallback description template.")
        description = build_fallback_description(product)

    return {
        "description": {
            "text": description,
            "seo_keywords": seo_keywords,
        }
    }


def _generate_promotion_node(state: _ProductState) -> dict[str, Any]:
    """Node: generate promotional text for the product."""
    product = {**state["product"], **state["categorization"]}
    promotion_type = state.get("promotion_type", "new_arrival")
    logger.info(
        "Generating %s promotion for: %s",
        promotion_type,
        product.get("name", "unknown"),
    )

    prompt = build_promotion_prompt(product, promotion_type)
    response = _invoke_llm(prompt)

    if response is not None:
        promotion = parse_promotion_response(response)
    else:
        logger.warning("Using fallback promotion template.")
        promotion = build_fallback_promotion(product)

    return {"promotion": promotion}


def _generate_image_node(state: _ProductState) -> dict[str, Any]:
    """Node: generate a themed image prompt for the product."""
    product = {**state["product"], **state["categorization"]}
    logger.info("Generating image prompt for: %s", product.get("name", "unknown"))

    theme = select_theme(product)
    image_prompt = build_image_prompt(product, theme)

    # Try to generate image via Gemini image generation
    image_url = None
    llm = _get_llm()
    if llm is not None:
        try:
            image_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
            )
            response = image_llm.invoke([HumanMessage(content=(
                "You are a product photography art director. "
                "Based on this photography brief, describe the ideal product image "
                "in vivid detail that could be used as an alt-text and visual guide "
                "for a photographer or image generation model.\n\n" + image_prompt
            ))])
            image_description = str(response.content)
        except Exception as exc:
            logger.warning("Image description generation failed: %s", exc)
            image_description = image_prompt
    else:
        image_description = image_prompt

    return {
        "image": {
            "prompt": image_prompt,
            "theme": theme,
            "image_description": image_description,
            "image_url": image_url,
        }
    }


# ---------------------------------------------------------------------------
# Build and compile the LangGraph workflow (module-level singleton)
# ---------------------------------------------------------------------------

_builder: StateGraph = StateGraph(cast(Any, _ProductState))
_builder.add_node("categorize", _categorize_node)
_builder.add_node("generate_description", _generate_description_node)
_builder.add_node("generate_promotion", _generate_promotion_node)
_builder.add_node("generate_image", _generate_image_node)

_builder.set_entry_point("categorize")
_builder.add_edge("categorize", "generate_description")
_builder.add_edge("categorize", "generate_promotion")
_builder.add_edge("categorize", "generate_image")
_builder.add_edge("generate_description", END)
_builder.add_edge("generate_promotion", END)
_builder.add_edge("generate_image", END)

_graph = _builder.compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_product(
    product: dict[str, Any],
    promotion_type: str = "new_arrival",
) -> dict[str, Any]:
    """Run the complete product-processing pipeline.

    The pipeline is implemented as a LangGraph StateGraph:
      1. ``categorize``            – classify product into category and style.
      2. ``generate_description``  – create SEO-friendly product description.
      3. ``generate_promotion``    – create promotional marketing text.
      4. ``generate_image``        – generate themed product image prompt.

    Steps 2, 3, 4 run in parallel after categorization completes.

    Args:
        product: Raw product payload from the API.
        promotion_type: Type of promotion to generate.

    Returns:
        Complete product enhancement dict containing:
          - ``product_name`` (str)
          - ``categorization`` (dict): category, style, tags, confidence
          - ``description`` (dict): text, seo_keywords
          - ``promotion`` (dict): headline, short_text, long_text, etc.
          - ``image`` (dict): prompt, theme, image_description
    """
    product_name = product.get("name", "unknown")
    logger.info("Starting product processing pipeline for: %s", product_name)

    initial_state: _ProductState = {
        "product": product,
        "promotion_type": promotion_type,
        "categorization": {},
        "description": {},
        "promotion": {},
        "image": {},
    }

    final_state = cast(_ProductState, _graph.invoke(initial_state))

    result: dict[str, Any] = {
        "product_name": product_name,
        "categorization": final_state["categorization"],
        "description": final_state["description"],
        "promotion": final_state["promotion"],
        "image": final_state["image"],
    }

    logger.info(
        "Product processing complete for %s: category=%s style=%s",
        product_name,
        final_state["categorization"].get("category", "unknown"),
        final_state["categorization"].get("style", "unknown"),
    )

    return result

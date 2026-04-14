"""Image analysis service using Gemini Vision.

Analyzes uploaded product photos to extract attributes such as
product type, material, color, style, and other visual details
that feed into the downstream pipeline.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from ceramicraft_product_agent.utils.logger import get_logger
from ceramicraft_product_agent.utils.mlflow_trace import trace

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Image analysis prompt
# ---------------------------------------------------------------------------

IMAGE_ANALYSIS_PROMPT = """\
You are a ceramic product expert. Analyze this product photo and extract \
detailed attributes for an e-commerce listing.

Respond STRICTLY in the following JSON format (no markdown, no extra text):
{{
  "name_suggestion": "<suggested product name based on what you see>",
  "material": "<detected material: porcelain, stoneware, earthenware, terracotta, bone china, ceramic, etc.>",
  "color": "<primary colors and glaze description>",
  "dimensions_estimate": "<estimated dimensions based on visual cues>",
  "description_hints": "<2-3 sentences describing what you see: shape, patterns, decorations, texture>",
  "attributes": {{
    "shape": "<product shape>",
    "pattern": "<decorative pattern if any>",
    "glaze": "<glaze type: matte, glossy, reactive, unglazed, etc.>",
    "technique": "<detected crafting technique if identifiable>",
    "condition": "<new, vintage, antique>"
  }}
}}
"""


@trace("gemini_vision_analyze")
def analyze_image_with_gemini(
    image_bytes: bytes,
    content_type: str,
    user_hints: str = "",
) -> dict[str, Any]:
    """Analyze a product image using Gemini Vision.

    Args:
        image_bytes: Raw image file bytes.
        content_type: MIME type (e.g. 'image/jpeg', 'image/png').
        user_hints: Optional text hints from the user about the product.

    Returns:
        Dict of extracted product attributes, or empty dict on failure.
    """
    import os

    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set – cannot analyze image.")
        return {}

    # Build multimodal message with image + text
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt_text = IMAGE_ANALYSIS_PROMPT
    if user_hints:
        prompt_text += f"\n\nAdditional context from the user: {user_hints}"

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{content_type};base64,{image_b64}"},
            },
            {
                "type": "text",
                "text": prompt_text,
            },
        ]
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key,
        )
        response = llm.invoke([message])
        return _parse_analysis_response(str(response.content))
    except Exception as exc:
        logger.error("Image analysis failed: %s", exc)
        return {}


def _parse_analysis_response(response_text: str) -> dict[str, Any]:
    """Parse the JSON response from Gemini image analysis."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        result = json.loads(cleaned)

        return {
            "name_suggestion": result.get("name_suggestion", ""),
            "material": result.get("material", "ceramic"),
            "color": result.get("color", ""),
            "dimensions_estimate": result.get("dimensions_estimate", ""),
            "description_hints": result.get("description_hints", ""),
            "attributes": result.get("attributes", {}),
        }
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to parse image analysis response: %s", exc)
        return {}

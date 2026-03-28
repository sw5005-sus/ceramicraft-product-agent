"""Templates for generating promotional text."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Gemini prompt template for promotional text generation
# ---------------------------------------------------------------------------

PROMOTION_PROMPT = """\
You are a marketing copywriter for CeramiCraft, a premium ceramics e-commerce \
platform. Create targeted promotional text for the following product.

Product Details:
- Name: {name}
- Category: {category}
- Style: {style}
- Material: {material}
- Price: {price}
- Tags: {tags}

Promotion Type: {promotion_type}

Generate the promotional content in the following JSON format (no markdown):
{{
  "headline": "<catchy headline, max 60 characters>",
  "short_text": "<social media / ad copy, max 150 characters>",
  "long_text": "<email or landing page promo, 2-3 sentences>",
  "call_to_action": "<CTA text, max 30 characters>",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}
"""

# ---------------------------------------------------------------------------
# Promotion types
# ---------------------------------------------------------------------------

PROMOTION_TYPES: dict[str, str] = {
    "new_arrival": "New product launch — emphasize freshness and exclusivity",
    "seasonal": "Seasonal promotion — tie to current season or holiday themes",
    "discount": "Discount sale — create urgency and highlight value",
    "collection": "Part of a curated collection — emphasize curation and pairing",
    "gift_guide": "Gift recommendation — focus on gifting appeal and occasions",
    "flash_sale": "Limited-time flash sale — create extreme urgency",
}

# ---------------------------------------------------------------------------
# Fallback promotional content
# ---------------------------------------------------------------------------

FALLBACK_PROMOTION = {
    "headline": "Discover {name} — Handcrafted Elegance",
    "short_text": "Elevate your space with the {name}. Premium {material} craftsmanship, {style} design.",
    "long_text": (
        "Introducing the {name}, a masterfully crafted {category} piece "
        "from CeramiCraft's curated collection. Made from premium {material}, "
        "this {style} creation brings timeless beauty to any setting."
    ),
    "call_to_action": "Shop Now",
    "hashtags": [
        "#CeramiCraft", "#Ceramics", "#{category}", "#{style}", "#HandmadeCeramics"
    ],
}

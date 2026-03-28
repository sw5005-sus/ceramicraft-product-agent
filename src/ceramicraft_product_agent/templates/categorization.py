"""Category definitions and classification rules for ceramic products."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Ceramic product category taxonomy
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, dict] = {
    "dinnerware": {
        "display_name": "Dinnerware",
        "description": "Plates, bowls, and serving pieces for dining",
        "keywords": [
            "plate", "bowl", "dish", "platter", "saucer", "charger",
            "dinner", "soup", "salad", "serving", "tureen", "gravy boat",
        ],
        "materials": ["porcelain", "stoneware", "earthenware", "bone china"],
    },
    "drinkware": {
        "display_name": "Drinkware",
        "description": "Cups, mugs, and vessels for beverages",
        "keywords": [
            "mug", "cup", "teacup", "goblet", "tumbler", "stein",
            "coffee", "tea", "espresso", "latte", "cappuccino",
        ],
        "materials": ["porcelain", "stoneware", "earthenware", "ceramic"],
    },
    "vases_decor": {
        "display_name": "Vases & Decorative",
        "description": "Vases, figurines, and decorative ceramic pieces",
        "keywords": [
            "vase", "figurine", "sculpture", "ornament", "centerpiece",
            "decorative", "flower", "display", "statue", "art piece",
        ],
        "materials": ["porcelain", "stoneware", "terracotta", "ceramic", "raku"],
    },
    "tea_sets": {
        "display_name": "Tea & Coffee Sets",
        "description": "Complete tea sets and coffee service sets",
        "keywords": [
            "tea set", "coffee set", "teapot", "creamer", "sugar bowl",
            "kettle", "infuser", "gaiwan", "yixing",
        ],
        "materials": ["porcelain", "stoneware", "yixing clay", "bone china"],
    },
    "kitchenware": {
        "display_name": "Kitchenware",
        "description": "Ceramic tools and containers for kitchen use",
        "keywords": [
            "jar", "canister", "butter dish", "spoon rest", "mortar",
            "pestle", "baking", "casserole", "ramekin", "pie dish",
            "storage", "container", "crock",
        ],
        "materials": ["stoneware", "earthenware", "porcelain", "ceramic"],
    },
    "tiles_panels": {
        "display_name": "Tiles & Wall Panels",
        "description": "Decorative and functional ceramic tiles",
        "keywords": [
            "tile", "panel", "mosaic", "backsplash", "wall art",
            "mural", "coaster", "trivet",
        ],
        "materials": ["ceramic", "porcelain", "terracotta", "majolica"],
    },
    "garden_outdoor": {
        "display_name": "Garden & Outdoor",
        "description": "Planters, garden pots, and outdoor ceramics",
        "keywords": [
            "planter", "pot", "garden", "outdoor", "birdbath",
            "lantern", "fountain", "urn",
        ],
        "materials": ["terracotta", "stoneware", "ceramic", "glazed ceramic"],
    },
}

# ---------------------------------------------------------------------------
# Style classification
# ---------------------------------------------------------------------------

STYLES: dict[str, list[str]] = {
    "traditional": [
        "classic", "traditional", "vintage", "antique", "heritage",
        "blue and white", "floral", "hand-painted", "delft", "chinoiserie",
    ],
    "modern": [
        "modern", "contemporary", "minimalist", "sleek", "geometric",
        "abstract", "clean lines", "monochrome",
    ],
    "rustic": [
        "rustic", "farmhouse", "handmade", "rough", "natural",
        "organic", "wabi-sabi", "imperfect", "artisan",
    ],
    "luxury": [
        "luxury", "premium", "gold", "gilded", "platinum",
        "fine china", "haute", "exclusive", "limited edition",
    ],
    "artistic": [
        "artistic", "creative", "unique", "one-of-a-kind", "studio",
        "raku", "crystalline", "glaze art", "sculptural",
    ],
}

# ---------------------------------------------------------------------------
# Prompt template for LLM-assisted categorization
# ---------------------------------------------------------------------------

CATEGORIZATION_PROMPT = """\
You are a ceramic product classification expert. Given the following product \
attributes, determine the best category, style, and relevant tags.

Product Name: {name}
Material: {material}
Description Hints: {description_hints}
Dimensions: {dimensions}
Additional Attributes: {attributes}

Available categories: {categories}
Available styles: {styles}

Respond STRICTLY in the following JSON format (no markdown, no extra text):
{{
  "category": "<category_key>",
  "style": "<style_key>",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "confidence": <0.0-1.0>
}}
"""

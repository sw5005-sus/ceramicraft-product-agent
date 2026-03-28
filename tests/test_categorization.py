"""Tests for the categorization service."""

from ceramicraft_product_agent.service.categorization import (
    classify_by_rules,
    parse_categorization_response,
)


class TestClassifyByRules:
    """Test rule-based categorization."""

    def test_teapot_classified_as_tea_sets(self):
        product = {
            "name": "Azure Dragon Teapot",
            "material": "porcelain",
            "description_hints": "traditional Chinese teapot",
        }
        result = classify_by_rules(product)
        assert result["category"] == "tea_sets"
        assert result["confidence"] > 0

    def test_mug_classified_as_drinkware(self):
        product = {
            "name": "Minimalist Coffee Mug",
            "material": "stoneware",
            "description_hints": "modern mug for coffee",
        }
        result = classify_by_rules(product)
        assert result["category"] == "drinkware"

    def test_platter_classified_as_dinnerware(self):
        product = {
            "name": "Rustic Serving Platter",
            "material": "earthenware",
            "description_hints": "large plate for serving dinner",
        }
        result = classify_by_rules(product)
        assert result["category"] == "dinnerware"

    def test_vase_classified_as_vases_decor(self):
        product = {
            "name": "Cherry Blossom Vase",
            "material": "porcelain",
            "description_hints": "decorative flower vase",
        }
        result = classify_by_rules(product)
        assert result["category"] == "vases_decor"

    def test_planter_classified_as_garden(self):
        product = {
            "name": "Terracotta Herb Garden Planter",
            "material": "terracotta",
            "description_hints": "garden planter for herbs outdoor",
        }
        result = classify_by_rules(product)
        assert result["category"] == "garden_outdoor"

    def test_result_contains_required_keys(self):
        product = {"name": "Test Product", "material": "ceramic"}
        result = classify_by_rules(product)
        assert "category" in result
        assert "style" in result
        assert "tags" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_tags_limited_to_8(self):
        product = {
            "name": "plate bowl dish platter saucer dinner soup salad serving tureen",
            "material": "porcelain",
            "description_hints": "many keywords",
        }
        result = classify_by_rules(product)
        assert len(result["tags"]) <= 8


class TestParseCategorizationResponse:
    """Test parsing of LLM categorization responses."""

    def test_valid_json_response(self):
        response = '{"category": "drinkware", "style": "modern", "tags": ["mug", "coffee"], "confidence": 0.9}'
        result = parse_categorization_response(response)
        assert result["category"] == "drinkware"
        assert result["style"] == "modern"
        assert result["confidence"] == 0.9

    def test_markdown_wrapped_json(self):
        response = '```json\n{"category": "tea_sets", "style": "traditional", "tags": ["teapot"], "confidence": 0.85}\n```'
        result = parse_categorization_response(response)
        assert result["category"] == "tea_sets"

    def test_invalid_category_fallback(self):
        response = '{"category": "invalid_cat", "style": "modern", "tags": [], "confidence": 0.5}'
        result = parse_categorization_response(response)
        assert result["category"] == "vases_decor"

    def test_invalid_json_fallback(self):
        response = "this is not json"
        result = parse_categorization_response(response)
        assert result["category"] == "vases_decor"
        assert result["confidence"] == 0.3

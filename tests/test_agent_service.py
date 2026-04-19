"""Tests for the agent service pipeline."""

from unittest.mock import patch

from ceramicraft_product_agent.service.agent_service import process_product

SAMPLE_PRODUCT = {
    "name": "Azure Dragon Teapot",
    "material": "porcelain",
    "dimensions": "18cm x 12cm x 14cm",
    "desc": "Hand-painted blue and white dragon motif, traditional Chinese style",
    "price": 8999,
    "stock": 50,
    "pic_info": "",
    "weight": "450g",
    "capacity": "500ml",
    "care_instructions": "Hand wash only",
    "category": "",
    "status": 0,
}


class TestProcessProduct:
    """Test the full product processing pipeline."""

    def test_pipeline_runs_without_api_key(self):
        """Pipeline should complete using fallbacks when no API key is set."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT)

        assert result["product_name"] == "Azure Dragon Teapot"
        assert "categorization" in result
        assert "description" in result
        assert "promotion" in result
        assert "image" in result
        assert "commodity_payload" in result
        payload = result["commodity_payload"]
        assert payload["name"] == "Azure Dragon Teapot"
        assert payload["price"] == 8999
        assert payload["material"] == "porcelain"

    def test_categorization_result_structure(self):
        """Categorization result should contain required fields."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT)

        cat = result["categorization"]
        assert "category" in cat
        assert "style" in cat
        assert "tags" in cat
        assert "confidence" in cat

    def test_description_result_structure(self):
        """Description result should contain text and seo_keywords."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT)

        desc = result["description"]
        assert "text" in desc
        assert "seo_keywords" in desc
        assert len(desc["text"]) > 0
        assert isinstance(desc["seo_keywords"], list)

    def test_promotion_result_structure(self):
        """Promotion result should contain all marketing fields."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT)

        promo = result["promotion"]
        assert "headline" in promo
        assert "short_text" in promo
        assert "long_text" in promo
        assert "call_to_action" in promo
        assert "hashtags" in promo

    def test_image_result_structure(self):
        """Image result should contain prompt, theme, and description."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT)

        img = result["image"]
        assert "prompt" in img
        assert "theme" in img
        assert "image_description" in img

    def test_promotion_type_passed_through(self):
        """Different promotion types should be accepted."""
        with patch.dict("os.environ", {}, clear=True):
            result = process_product(SAMPLE_PRODUCT, promotion_type="seasonal")

        assert result["product_name"] == "Azure Dragon Teapot"

    @patch("ceramicraft_product_agent.service.agent_service._invoke_llm")
    def test_pipeline_with_mocked_llm(self, mock_llm):
        """Pipeline should work with mocked LLM responses."""
        mock_llm.side_effect = [
            # categorization response
            '{"category": "tea_sets", "style": "traditional", "tags": ["teapot", "dragon"], "confidence": 0.95}',
            # SEO keywords response
            '["porcelain teapot", "dragon teapot", "chinese ceramic"]',
            # description response
            "A beautifully crafted teapot with dragon motifs.",
            # promotion response
            '{"headline": "New: Dragon Teapot", "short_text": "Exquisite teapot", "long_text": "Discover this beauty.", "call_to_action": "Shop Now", "hashtags": ["#teapot"]}',
            # image description response
            "A stunning blue and white porcelain teapot photographed on a wooden table.",
        ]

        result = process_product(SAMPLE_PRODUCT)
        assert result["categorization"]["category"] == "tea_sets"
        assert result["categorization"]["confidence"] == 0.95

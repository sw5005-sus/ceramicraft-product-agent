"""Templates for generating SEO-friendly product descriptions."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Gemini prompt template for product description generation
# ---------------------------------------------------------------------------

DESCRIPTION_PROMPT = """\
You are a professional copywriter for a premium ceramics e-commerce platform \
called CeramiCraft. Write a compelling, SEO-friendly product description.

Product Details:
- Name: {name}
- Category: {category}
- Style: {style}
- Material: {material}
- Dimensions: {dimensions}
- Tags: {tags}
- Additional Attributes: {attributes}

Requirements:
1. Write exactly 3 paragraphs.
2. Paragraph 1: Hook the reader with the product's unique appeal and craftsmanship.
3. Paragraph 2: Detail the material, dimensions, and functional benefits.
4. Paragraph 3: Suggest use cases and gifting occasions.
5. Naturally include these SEO keywords: {seo_keywords}
6. Tone: warm, sophisticated, and inviting.
7. Do NOT use markdown formatting. Use plain text only.

Respond STRICTLY with the description text only, no titles or labels.
"""

# ---------------------------------------------------------------------------
# Fallback description template (when Gemini API is unavailable)
# ---------------------------------------------------------------------------

FALLBACK_DESCRIPTION = """\
Discover the exquisite {name}, a stunning {style} {category} piece crafted \
from premium {material}. This beautifully designed ceramic creation measures \
{dimensions}, making it a perfect addition to any space.

Built with meticulous attention to detail, the {name} showcases the finest \
qualities of {material} craftsmanship. Its {style} aesthetic brings both \
elegance and functionality to your home, whether displayed as a centerpiece \
or used in everyday life.

An ideal gift for ceramic enthusiasts, housewarmings, or special occasions, \
this piece embodies the artistry and heritage of fine ceramic making. \
Add the {name} to your collection and experience the timeless beauty of \
handcrafted ceramics.
"""

# ---------------------------------------------------------------------------
# SEO keyword generation prompt
# ---------------------------------------------------------------------------

SEO_KEYWORDS_PROMPT = """\
Generate 8 SEO keywords for a ceramic product with these attributes:
- Name: {name}
- Category: {category}
- Style: {style}
- Material: {material}

Respond with a JSON array of strings only, no extra text.
Example: ["keyword1", "keyword2", "keyword3"]
"""

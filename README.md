# ceramicraft-product-agent

AI-powered Product Agent for the CeramiCraft platform. Assists B-side administrators in streamlining ceramic product listing and management.

## Features

- **Auto-Categorization**: Classifies ceramic products into categories (dinnerware, drinkware, vases, tea sets, etc.) and styles using keyword heuristics + Gemini LLM
- **SEO Description Generation**: Creates compelling, SEO-friendly product descriptions with targeted keywords
- **Promotional Text Generation**: Generates marketing copy (headlines, social media text, email copy) for multiple promotion types
- **Image Prompt Generation**: Creates themed product photography prompts for image generation

## Architecture

LangGraph-based pipeline with Gemini LLM integration:

```
categorize → generate_description ↘
           → generate_promotion   → END
           → generate_image       ↗
```

Steps 2-4 run in parallel after categorization completes.

## Quick Start

```bash
# Install dependencies
uv sync

# Set Gemini API key (optional - falls back to rule-based generation)
export GOOGLE_API_KEY=your_api_key_here

# Run the server
uv run python -m ceramicraft_product_agent.app

# Run tests
uv run pytest tests/ -v
```

## API Endpoints

- `POST /product/process` — Process a single product
- `POST /product/batch` — Process multiple products
- `GET /health` — Health check

## Example Request

```json
POST /product/process
{
  "name": "Azure Dragon Teapot",
  "material": "porcelain",
  "dimensions": "18cm x 12cm x 14cm",
  "description_hints": "Hand-painted blue and white dragon motif",
  "color": "blue and white",
  "price": "$89.99",
  "attributes": {"origin": "Jingdezhen", "technique": "hand-painted"},
  "promotion_type": "new_arrival"
}
```

## Docker

```bash
docker build -t ceramicraft-product-agent .
docker run -p 8001:8001 -e GOOGLE_API_KEY=your_key ceramicraft-product-agent
```

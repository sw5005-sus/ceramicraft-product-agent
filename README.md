# ceramicraft-product-agent

AI-powered Product Agent for the CeramiCraft e-commerce platform. Assists B-side merchant administrators in streamlining ceramic product listing and management by generating AI-enhanced product content.

---

## Features

- **Auto-Categorization**: Classifies ceramic products into categories (dinnerware, drinkware, vases, tea sets, etc.) and styles using keyword heuristics + Gemini LLM
- **SEO Description Generation**: Creates compelling, SEO-friendly product descriptions with targeted keywords
- **Promotional Text Generation**: Generates marketing copy (headlines, social media text, email copy) for multiple promotion types
- **Image Prompt Generation**: Creates themed product photography prompts for image generation
- **Image Analysis**: Analyzes uploaded product photos via Gemini Vision to extract attributes
- **JWT Authentication**: Role-based access control compatible with `ceramicraft-user-mservice`
- **Commodity Service Integration**: Output payload directly aligned with `ceramicraft-commodity-mservice` ProductInfo schema

---

## Architecture

LangGraph-based pipeline with Gemini LLM integration:

```
                           ┌─ generate_description ─┐
Input → categorize ───────►├─ generate_promotion   ─┼──► Output (commodity_payload + AI content)
                           └─ generate_image       ─┘
```

Steps 2-4 run in parallel after categorization completes.

### Package Structure

```
src/ceramicraft_product_agent/
├── api/
│   └── product_api.py          # FastAPI router – /product endpoints
├── middleware/
│   └── auth.py                 # JWT authentication & RBAC middleware
├── service/
│   ├── agent_service.py        # LangGraph orchestrator (main pipeline)
│   ├── categorization.py       # Product categorization logic
│   ├── description_gen.py      # SEO description generation
│   ├── promotion_gen.py        # Marketing copy generation
│   ├── image_gen.py            # Image prompt generation
│   └── image_analysis.py       # Gemini Vision image analysis
├── templates/
│   ├── categorization.py       # Categorization prompt templates
│   ├── description.py          # Description prompt templates
│   └── promotion.py            # Promotion prompt templates
├── utils/
│   └── logger.py               # Logging utilities
├── data/
│   └── mock_data.json          # Sample data for testing
├── static/
│   └── index.html              # Frontend demo page
└── app.py                      # FastAPI application entry point
```

---

## Data Schema Alignment

The request/response schemas are aligned with `ceramicraft-commodity-mservice` `ProductInfo`:

| Field              | Type   | Description                              |
|--------------------|--------|------------------------------------------|
| `name`             | string | Product name                             |
| `category`         | string | Product category (auto-categorized if empty) |
| `price`            | int    | Price in cents (e.g. 8999 = $89.99)      |
| `desc`             | string | Product description / hints              |
| `stock`            | int    | Stock quantity                           |
| `pic_info`         | string | Product image URLs (JSON string)         |
| `dimensions`       | string | Product dimensions                       |
| `material`         | string | Primary material                         |
| `weight`           | string | Product weight                           |
| `capacity`         | string | Product capacity                         |
| `care_instructions`| string | Care and maintenance instructions        |
| `status`           | int    | 0: unpublished, 1: published             |
| `promotion_type`   | string | Agent-specific: promotion type to generate |

The response includes a `commodity_payload` field that can be sent directly to `POST /product-ms/v1/merchant/products`.

---

## Authentication

All `/product` endpoints require JWT authentication, compatible with `ceramicraft-user-mservice`.

- **Header**: `Authorization: Bearer <token>`
- **Required Roles**: `merchant_admin` or `product_editor`
- **Environment Variable**: `JWT_SECRET` (must match the secret used by `ceramicraft-user-mservice`)

The JWT token payload is expected to contain:
```json
{
  "user_id": "123",
  "role": "merchant_admin",
  "exp": 1700000000
}
```

Unauthenticated endpoints: `GET /health`, `GET /` (demo page)

---

## API Endpoints

| Method | Path                        | Auth Required | Description                      |
|--------|-----------------------------|---------------|----------------------------------|
| POST   | `/product/process`          | Yes           | Process a single product         |
| POST   | `/product/batch`            | Yes           | Process multiple products        |
| POST   | `/product/process-with-image`| Yes          | Process with uploaded photo      |
| GET    | `/health`                   | No            | Health check                     |
| GET    | `/`                         | No            | Demo frontend page               |

---

## Quick Start

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment
```bash
# Required for AI features (falls back to rule-based if not set)
export GOOGLE_API_KEY=your_gemini_api_key

# Required for authentication
export JWT_SECRET=your_jwt_secret
```

### 3. Start the server
```bash
uv run python -m ceramicraft_product_agent.app
```

### 4. Test the API
```bash
curl -X POST http://127.0.0.1:8001/product/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "name": "Azure Dragon Teapot",
    "category": "",
    "price": 8999,
    "desc": "Hand-painted blue and white dragon motif, traditional Chinese style",
    "stock": 50,
    "pic_info": "",
    "dimensions": "18cm x 12cm x 14cm",
    "material": "porcelain",
    "weight": "450g",
    "capacity": "500ml",
    "care_instructions": "Hand wash only, do not microwave",
    "status": 0,
    "promotion_type": "new_arrival"
  }'
```

### 5. Run tests
```bash
uv run pytest tests/ -v
```

---

## Example Response

```json
{
  "product_name": "Azure Dragon Teapot",
  "commodity_payload": {
    "name": "Azure Dragon Teapot",
    "category": "tea_sets",
    "price": 8999,
    "desc": "Discover the Azure Dragon Teapot — a masterfully hand-painted porcelain ...",
    "stock": 50,
    "pic_info": "",
    "dimensions": "18cm x 12cm x 14cm",
    "material": "porcelain",
    "weight": "450g",
    "capacity": "500ml",
    "care_instructions": "Hand wash only, do not microwave",
    "status": 0
  },
  "categorization": {
    "category": "tea_sets",
    "style": "traditional",
    "tags": ["teapot", "dragon", "hand-painted", "porcelain"],
    "confidence": 0.92
  },
  "description": {
    "text": "Discover the Azure Dragon Teapot ...",
    "seo_keywords": ["porcelain teapot", "hand-painted ceramic", ...]
  },
  "promotion": {
    "headline": "Introducing the Azure Dragon Teapot",
    "short_text": "Elevate your tea ritual with this hand-painted masterpiece.",
    "long_text": "...",
    "call_to_action": "Shop Now",
    "hashtags": ["#CeramiCraft", "#Porcelain", "#TeaSet"]
  },
  "image": {
    "prompt": "Generate a professional e-commerce product photograph ...",
    "theme": "rustic_table",
    "image_description": "...",
    "image_url": null
  }
}
```

---

## Observability

### OpenTelemetry (log / trace / metric)

The service is wired to emit OTLP telemetry. In Docker it auto-starts via
`opentelemetry-instrument`, so no code changes are needed to enable tracing —
just set the endpoint at deploy time:

| Env var | Purpose |
|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector endpoint, e.g. `http://grafana-alloy.monitoring.svc.cluster.local:4317` |
| `OTEL_SERVICE_NAME` | Service name (default `ceramicraft-product-agent`) |
| `OTEL_PYTHON_LOG_CORRELATION` | Inject `trace_id` / `span_id` into log lines (default `true`) |

Log lines include trace correlation fields:
```
2026-04-14T10:00:00 INFO [ceramicraft_product_agent.service.agent_service] [trace_id=4f2a... span_id=9b81...] - Starting product processing pipeline for: Azure Dragon Teapot
```

### MLflow LLM tracing

Every LangGraph node and each Gemini invocation is recorded as an MLflow trace
span (latency, prompt length, fallback flag). Disabled by default — opt in with:

```bash
export ENABLE_MLFLOW_TRACING=true
export MLFLOW_TRACKING_URI=http://mlflow.example:5000
export MLFLOW_EXPERIMENT_NAME=product-agent-llm-traces   # optional
```

When disabled, `@trace` is a no-op (zero overhead, safe for CI / local dev).

---

## Docker

```bash
docker build -t ceramicraft-product-agent .
docker run -p 8001:8001 \
  -e GOOGLE_API_KEY=your_key \
  -e JWT_SECRET=your_secret \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://grafana-alloy:4317 \
  -e ENABLE_MLFLOW_TRACING=true \
  -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
  ceramicraft-product-agent
```

---

## CI/CD & Deployment

- **Test & Lint**: Automated via GitHub Actions on push/PR to `main`
- **Deploy**: Manual trigger via `deploy.yml` workflow
  1. Builds Docker image and pushes to DockerHub
  2. Updates ArgoCD deploy repo (`ceramicraft-argocd-deploy`) with new image tag
- **Required Secrets**: `DOCKER_HUB_USERNAME`, `DOCKER_HUB_ACCESS_TOKEN`, `PAT_TOKEN`

---

## Integration with Other Services

| Service                       | Integration                                         |
|-------------------------------|-----------------------------------------------------|
| `ceramicraft-commodity-mservice` | `commodity_payload` output matches `ProductInfo` schema |
| `ceramicraft-user-mservice`   | JWT auth with shared `JWT_SECRET`                   |
| `ceramicraft-ai-secure-agent` | Shared LangGraph architecture pattern               |
| Prometheus / Grafana          | Health check endpoint for monitoring                |

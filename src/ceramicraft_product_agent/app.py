"""FastAPI application entry point for the Product Agent."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ceramicraft_product_agent.api.product_api import router as product_router
from ceramicraft_product_agent.utils.logger import get_logger

# Auto-load .env from project root if present (for local dev)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

logger = get_logger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Product Agent – Ceramic Product Enhancement API",
    description=(
        "AI-powered product listing agent that generates SEO-friendly "
        "descriptions, promotional text, auto-categorization, and themed "
        "image prompts for ceramic products using Google Gemini.\n\n"
        "All /product endpoints require JWT authentication (Bearer token) "
        "with merchant_admin or product_editor role."
    ),
    version="2.0.0",
)

app.include_router(product_router)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def index():
    """Serve the frontend demo page."""
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return a simple health-check response."""
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8080))
    logger.info("Starting Product Agent API server on %s:%s ...", host, port)
    uvicorn.run("ceramicraft_product_agent.app:app", host=host, port=port, reload=False)

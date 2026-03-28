"""FastAPI application entry point for the Product Agent."""

from __future__ import annotations

from fastapi import FastAPI

from ceramicraft_product_agent.api.product_api import router as product_router
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Product Agent – Ceramic Product Enhancement API",
    description=(
        "AI-powered product listing agent that generates SEO-friendly "
        "descriptions, promotional text, auto-categorization, and themed "
        "image prompts for ceramic products using Google Gemini."
    ),
    version="1.0.0",
)

app.include_router(product_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Return a simple health-check response."""
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8001))
    logger.info("Starting Product Agent API server on %s:%s ...", host, port)
    uvicorn.run(
        "ceramicraft_product_agent.app:app", host=host, port=port, reload=False
    )

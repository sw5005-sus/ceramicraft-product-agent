"""FastAPI router for the /product endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceramicraft_product_agent.service.agent_service import process_product
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/product", tags=["Product"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ProductRequest(BaseModel):
    """Schema for an incoming product processing request."""

    name: str = Field(..., description="Product name")
    material: str = Field(default="ceramic", description="Primary material")
    dimensions: str = Field(default="", description="Product dimensions (e.g. '10cm x 8cm')")
    description_hints: str = Field(
        default="", description="Brief hints or notes about the product"
    )
    color: str = Field(default="", description="Primary color or glaze")
    price: str = Field(default="", description="Price (e.g. '$49.99')")
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Additional key-value attributes (e.g. origin, technique)",
    )
    promotion_type: str = Field(
        default="new_arrival",
        description="Promotion type: new_arrival, seasonal, discount, collection, gift_guide, flash_sale",
    )


class CategorizationResult(BaseModel):
    """Categorization sub-result."""

    category: str
    style: str
    tags: list[str]
    confidence: float


class DescriptionResult(BaseModel):
    """Description sub-result."""

    text: str
    seo_keywords: list[str]


class PromotionResult(BaseModel):
    """Promotion sub-result."""

    headline: str
    short_text: str
    long_text: str
    call_to_action: str
    hashtags: list[str]


class ImageResult(BaseModel):
    """Image generation sub-result."""

    prompt: str
    theme: str
    image_description: str
    image_url: str | None = None


class ProductResponse(BaseModel):
    """Schema for the /product/process response."""

    product_name: str
    categorization: CategorizationResult
    description: DescriptionResult
    promotion: PromotionResult
    image: ImageResult


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/process",
    response_model=ProductResponse,
    summary="Process a new product listing",
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Product processing failed."}
                }
            },
        }
    },
)
async def process_product_endpoint(request: ProductRequest) -> Any:
    """Process a product through the full enhancement pipeline.

    Runs auto-categorization, description generation, promotional text
    creation, and image prompt generation for a ceramic product.
    """
    safe_name = request.name.replace("\n", "").replace("\r", "")[:100]
    logger.info("Received product processing request for: %s", safe_name)
    try:
        result = process_product(
            product=request.model_dump(),
            promotion_type=request.promotion_type,
        )
    except Exception as exc:
        logger.error(
            "Product processing failed for %s: %s",
            safe_name,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Product processing failed."
        ) from exc

    return result


@router.post(
    "/batch",
    response_model=list[ProductResponse],
    summary="Process multiple products",
)
async def batch_process_endpoint(requests: list[ProductRequest]) -> Any:
    """Process multiple products through the enhancement pipeline."""
    logger.info("Received batch request for %d products", len(requests))
    results = []
    for req in requests:
        safe_name = req.name.replace("\n", "").replace("\r", "")[:100]
        try:
            result = process_product(
                product=req.model_dump(),
                promotion_type=req.promotion_type,
            )
            results.append(result)
        except Exception as exc:
            logger.error("Failed to process %s: %s", safe_name, exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Product processing failed for: {safe_name}",
            ) from exc

    return results

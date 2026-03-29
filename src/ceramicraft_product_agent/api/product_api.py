"""FastAPI router for the /product endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ceramicraft_product_agent.service.agent_service import process_product
from ceramicraft_product_agent.service.image_analysis import analyze_image_with_gemini
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


class ImageAnalysisResult(BaseModel):
    """Image analysis sub-result."""

    name_suggestion: str = ""
    material: str = ""
    color: str = ""
    dimensions_estimate: str = ""
    description_hints: str = ""
    attributes: dict[str, str] = {}


class ProductResponse(BaseModel):
    """Schema for the /product/process response."""

    product_name: str
    image_analysis: ImageAnalysisResult | None = None
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


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post(
    "/process-with-image",
    response_model=ProductResponse,
    summary="Process a product with an uploaded photo",
)
async def process_with_image_endpoint(
    image: UploadFile = File(..., description="Product photo (JPEG/PNG/WebP)"),
    name: str = Form(default="", description="Product name (optional, auto-detected from image)"),
    material: str = Form(default="", description="Material (optional, auto-detected from image)"),
    dimensions: str = Form(default="", description="Dimensions"),
    color: str = Form(default="", description="Color"),
    price: str = Form(default="", description="Price"),
    description_hints: str = Form(default="", description="Additional hints about the product"),
    promotion_type: str = Form(default="new_arrival", description="Promotion type"),
) -> Any:
    """Process a product with an uploaded sample photo.

    The photo is analyzed by Gemini Vision to extract product attributes
    (name, material, color, style, etc.), which are then merged with any
    user-provided fields and fed into the full enhancement pipeline.
    """
    # Validate image
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

    logger.info(
        "Received image upload: %s (%s, %d bytes)",
        image.filename,
        image.content_type,
        len(image_bytes),
    )

    # Step 1: Analyze image with Gemini Vision
    analysis = analyze_image_with_gemini(
        image_bytes=image_bytes,
        content_type=image.content_type or "image/jpeg",
        user_hints=description_hints,
    )
    logger.info("Image analysis result: %s", analysis)

    # Step 2: Merge — user-provided fields take priority, image analysis fills gaps
    product = {
        "name": name or analysis.get("name_suggestion", "Ceramic Product"),
        "material": material or analysis.get("material", "ceramic"),
        "dimensions": dimensions or analysis.get("dimensions_estimate", ""),
        "color": color or analysis.get("color", ""),
        "price": price,
        "description_hints": " ".join(filter(None, [
            description_hints,
            analysis.get("description_hints", ""),
        ])),
        "attributes": analysis.get("attributes", {}),
        "promotion_type": promotion_type,
    }

    safe_name = product["name"].replace("\n", "").replace("\r", "")[:100]
    logger.info("Processing product from image: %s", safe_name)

    # Step 3: Run the full pipeline
    try:
        result = process_product(
            product=product,
            promotion_type=promotion_type,
        )
        result["image_analysis"] = analysis
    except Exception as exc:
        logger.error(
            "Product processing failed for %s: %s", safe_name, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Product processing failed."
        ) from exc

    return result

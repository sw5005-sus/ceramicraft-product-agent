"""FastAPI router for the /product endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ceramicraft_product_agent.grpc_client.commodity_client import (
    create_product as grpc_create_product,
)
from ceramicraft_product_agent.middleware.auth import require_roles
from ceramicraft_product_agent.service.agent_service import process_product
from ceramicraft_product_agent.service.image_analysis import analyze_image_with_gemini
from ceramicraft_product_agent.service.s3_upload import upload_image
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/product", tags=["Product"])


# ---------------------------------------------------------------------------
# Request / Response schemas  (aligned with commodity-mservice ProductInfo)
# ---------------------------------------------------------------------------


class ProductRequest(BaseModel):
    """Schema aligned with commodity-mservice ProductInfo fields."""

    name: str = Field(..., description="Product name")
    category: str = Field(
        default="", description="Product category (auto-categorized if empty)"
    )
    price: int = Field(default=0, description="Product price in cents (int64)")
    desc: str = Field(
        default="", description="Product description or hints for generation"
    )
    stock: int = Field(default=0, description="Stock quantity")
    pic_info: str = Field(default="", description="Product image URLs (JSON string)")
    dimensions: str = Field(
        default="", description="Product dimensions (e.g. '10cm x 8cm')"
    )
    material: str = Field(default="ceramic", description="Primary material")
    weight: str = Field(default="", description="Product weight")
    capacity: str = Field(default="", description="Product capacity (e.g. '500ml')")
    care_instructions: str = Field(
        default="", description="Care and maintenance instructions"
    )
    status: int = Field(
        default=0, description="Product status: 0=unpublished, 1=published"
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


class CommodityProductPayload(BaseModel):
    """Payload formatted for commodity-mservice ProductInfo API."""

    name: str
    category: str
    price: int
    desc: str
    stock: int
    pic_info: str
    dimensions: str
    material: str
    weight: str
    capacity: str
    care_instructions: str
    status: int


class ProductResponse(BaseModel):
    """Schema for the /product/process response."""

    product_name: str
    commodity_payload: CommodityProductPayload
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
async def process_product_endpoint(
    request: ProductRequest,
    user: dict = Depends(require_roles("merchant_admin", "product_editor")),
) -> Any:
    """Process a product through the full enhancement pipeline.

    Requires merchant_admin or product_editor role (JWT auth).
    Runs auto-categorization, description generation, promotional text
    creation, and image prompt generation for a ceramic product.
    """
    safe_name = request.name.replace("\n", "").replace("\r", "")[:100]
    logger.info(
        "Received product processing request for: %s (user: %s)",
        safe_name,
        user.get("user_id"),
    )
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
async def batch_process_endpoint(
    requests: list[ProductRequest],
    user: dict = Depends(require_roles("merchant_admin", "product_editor")),
) -> Any:
    """Process multiple products through the enhancement pipeline."""
    logger.info(
        "Received batch request for %d products (user: %s)",
        len(requests),
        user.get("user_id"),
    )
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
    name: str = Form(
        default="", description="Product name (optional, auto-detected from image)"
    ),
    category: str = Form(
        default="", description="Product category (optional, auto-categorized)"
    ),
    price: int = Form(default=0, description="Price in cents"),
    desc: str = Form(default="", description="Description or hints"),
    stock: int = Form(default=0, description="Stock quantity"),
    pic_info: str = Form(default="", description="Existing image URLs"),
    dimensions: str = Form(default="", description="Dimensions"),
    material: str = Form(default="", description="Material"),
    weight: str = Form(default="", description="Weight"),
    capacity: str = Form(default="", description="Capacity"),
    care_instructions: str = Form(default="", description="Care instructions"),
    status: int = Form(default=0, description="Status: 0=unpublished, 1=published"),
    promotion_type: str = Form(default="new_arrival", description="Promotion type"),
    user: dict = Depends(require_roles("merchant_admin", "product_editor")),
) -> Any:
    """Process a product with an uploaded sample photo.

    Requires merchant_admin or product_editor role (JWT auth).
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
        "Received image upload: %s (%s, %d bytes, user: %s)",
        image.filename,
        image.content_type,
        len(image_bytes),
        user.get("user_id"),
    )

    # Step 1: Upload image to S3
    image_id = ""
    try:
        image_id = upload_image(image_bytes, image.content_type or "image/jpeg")
        logger.info("Image uploaded to S3: %s", image_id)
    except Exception as exc:
        logger.warning("S3 upload failed, continuing without image: %s", exc)

    # Step 2: Analyze image with Gemini Vision
    analysis = analyze_image_with_gemini(
        image_bytes=image_bytes,
        content_type=image.content_type or "image/jpeg",
        user_hints=desc,
    )
    logger.info("Image analysis result: %s", analysis)

    # Step 3: Merge — user-provided fields take priority, image analysis fills gaps
    merged_pic_info = pic_info or (f'["{image_id}"]' if image_id else "")
    product = {
        "name": name or analysis.get("name_suggestion", "Ceramic Product"),
        "category": category,
        "price": price,
        "desc": " ".join(
            filter(
                None,
                [
                    desc,
                    analysis.get("description_hints", ""),
                ],
            )
        ),
        "stock": stock,
        "pic_info": merged_pic_info,
        "dimensions": dimensions or analysis.get("dimensions_estimate", ""),
        "material": material or analysis.get("material", "ceramic"),
        "weight": weight,
        "capacity": capacity,
        "care_instructions": care_instructions,
        "status": status,
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


# ---------------------------------------------------------------------------
# Process + Save to commodity-mservice via gRPC
# ---------------------------------------------------------------------------


class SavedProductResponse(BaseModel):
    """Response for process-and-save: includes AI content + DB record."""

    product_name: str
    product_id: int
    commodity_payload: CommodityProductPayload
    categorization: CategorizationResult
    description: DescriptionResult
    promotion: PromotionResult
    image: ImageResult


@router.post(
    "/process-and-save",
    response_model=SavedProductResponse,
    summary="Process product and save to commodity service",
)
async def process_and_save_endpoint(
    request: ProductRequest,
    user: dict = Depends(require_roles("merchant_admin", "product_editor")),
) -> Any:
    """Generate AI content and save the product to commodity-mservice via gRPC.

    Full pipeline: Gemini enhancement -> gRPC CreateProduct -> return with DB id.
    """
    safe_name = request.name.replace("\n", "").replace("\r", "")[:100]
    editor_id = int(user.get("user_id", 0))
    logger.info("Process-and-save for: %s (user: %s)", safe_name, editor_id)

    try:
        result = process_product(
            product=request.model_dump(),
            promotion_type=request.promotion_type,
        )
    except Exception as exc:
        logger.error("Pipeline failed for %s: %s", safe_name, exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Product processing failed."
        ) from exc

    try:
        saved = grpc_create_product(result["commodity_payload"], editor_id=editor_id)
    except Exception as exc:
        logger.error("gRPC CreateProduct failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Product generated but failed to save: {exc}",
        ) from exc

    return {
        "product_name": result["product_name"],
        "product_id": saved["id"],
        "commodity_payload": saved,
        "categorization": result["categorization"],
        "description": result["description"],
        "promotion": result["promotion"],
        "image": result["image"],
    }

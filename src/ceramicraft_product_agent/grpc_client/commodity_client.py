"""gRPC client for ceramicraft-commodity-mservice.

Calls CreateProduct RPC to persist AI-generated product content
directly into the commodity service database.
"""

from __future__ import annotations

import os
from typing import Any

import grpc

from ceramicraft_product_agent.grpc_client import product_pb2, product_pb2_grpc
from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)


def _get_channel_target() -> str:
    host = os.environ.get("COMMODITY_GRPC_HOST", "127.0.0.1")
    port = os.environ.get("COMMODITY_GRPC_PORT", "5001")
    return f"{host}:{port}"


def create_product(payload: dict[str, Any], editor_id: int = 0) -> dict[str, Any]:
    """Create a product in commodity-mservice via gRPC.

    Args:
        payload: commodity_payload dict from the product agent pipeline.
        editor_id: The user ID of the merchant creating the product.

    Returns:
        Dict with created product info including the assigned ``id``.

    Raises:
        grpc.RpcError: On gRPC communication failure.
    """
    target = _get_channel_target()
    logger.info("Calling CreateProduct gRPC at %s for: %s", target, payload.get("name"))

    request = product_pb2.CreateProductRequest(
        name=payload.get("name", ""),
        category=payload.get("category", ""),
        price=payload.get("price", 0),
        desc=payload.get("desc", ""),
        stock=payload.get("stock", 0),
        picInfo=payload.get("pic_info", ""),
        dimensions=payload.get("dimensions", ""),
        material=payload.get("material", ""),
        weight=payload.get("weight", ""),
        capacity=payload.get("capacity", ""),
        careInstructions=payload.get("care_instructions", ""),
        latestEditorId=editor_id,
    )

    with grpc.insecure_channel(target) as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)
        response = stub.CreateProduct(request, timeout=10)

    if response.base and response.base.code != 0:
        logger.error(
            "CreateProduct failed: code=%d msg=%s",
            response.base.code,
            response.base.msg,
        )
        raise RuntimeError(f"CreateProduct RPC failed: {response.base.msg}")

    logger.info(
        "Product created successfully: id=%d name=%s", response.id, response.name
    )

    return {
        "id": response.id,
        "name": response.name,
        "category": response.category,
        "price": response.price,
        "desc": response.desc,
        "stock": response.stock,
        "pic_info": response.picInfo,
        "dimensions": response.dimensions,
        "material": response.material,
        "weight": response.weight,
        "capacity": response.capacity,
        "care_instructions": response.careInstructions,
        "status": 0,
    }

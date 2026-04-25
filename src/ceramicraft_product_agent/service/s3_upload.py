"""S3 image upload service.

Uploads product images to the ceramicraft S3 bucket and returns
the image_id (object key) for storage in pic_info.
"""

from __future__ import annotations

import os
import time

import boto3

from ceramicraft_product_agent.utils.logger import get_logger

logger = get_logger(__name__)

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=os.environ.get("S3_REGION", "ap-southeast-1"),
        )
    return _s3_client


def upload_image(
    image_bytes: bytes,
    content_type: str = "image/jpeg",
) -> str:
    """Upload image bytes to S3 and return the object key (image_id).

    The object key format matches commodity-mservice convention:
    ``{hex_timestamp}.{extension}``

    Returns:
        The S3 object key (e.g. ``"1870d5478d6b226b.png"``).
    """
    ext_map = {
        "image/jpeg": "jpeg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(content_type, "jpg")
    object_key = f"{time.time_ns():x}.{ext}"
    bucket = os.environ.get("S3_BUCKET", "ceramicraft")

    logger.info(
        "Uploading image to s3://%s/%s (%d bytes)", bucket, object_key, len(image_bytes)
    )

    client = _get_s3_client()
    client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=image_bytes,
        ContentType=content_type,
    )

    logger.info("Image uploaded successfully: %s", object_key)
    return object_key

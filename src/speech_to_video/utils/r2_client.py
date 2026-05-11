"""Cloudflare R2 client (S3-compatible) for V2 template asset hosting.

Public-read bucket; objects served via the custom domain configured at
R2_PUBLIC_BASE_URL (default `https://assets.speech-2-video.ai`). Long-TTL
cache (1 year, immutable) — assets are versioned by key, never overwritten.

boto3 client is lazy-init from R2_ACCOUNT_ID / R2_ACCESS_KEY_ID /
R2_SECRET_ACCESS_KEY. Calls raise R2NotConfigured if any of those are unset.
"""
from __future__ import annotations

import logging
import mimetypes
import os
from typing import Any, Dict, Optional

from .config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_CACHE_CONTROL = "public, max-age=31536000, immutable"

_client = None


class R2NotConfigured(RuntimeError):
    """R2 credentials are not set in the environment."""


def _s3():
    global _client
    if _client is not None:
        return _client
    s = get_settings()
    if not (s.r2_account_id and s.r2_access_key_id and s.r2_secret_access_key):
        raise R2NotConfigured(
            "R2 credentials missing — set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY"
        )
    import boto3
    _client = boto3.client(
        "s3",
        endpoint_url=f"https://{s.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=s.r2_access_key_id,
        aws_secret_access_key=s.r2_secret_access_key,
        region_name="auto",
    )
    return _client


def public_url(key: str) -> str:
    """Public URL for a key under the custom domain."""
    base = get_settings().r2_public_base_url.rstrip("/")
    return f"{base}/{key.lstrip('/')}"


def upload_file(
    local_path: str,
    key: str,
    content_type: Optional[str] = None,
    cache_control: str = DEFAULT_CACHE_CONTROL,
) -> str:
    """Upload a local file to R2; returns the public URL."""
    if content_type is None:
        guessed, _ = mimetypes.guess_type(local_path)
        content_type = guessed or "application/octet-stream"
    extra = {"CacheControl": cache_control, "ContentType": content_type}
    bucket = get_settings().r2_bucket
    _s3().upload_file(local_path, bucket, key, ExtraArgs=extra)
    logger.info(
        "R2 upload: %s -> r2://%s/%s (%s)",
        os.path.basename(local_path), bucket, key, content_type,
    )
    return public_url(key)


def head_object(key: str) -> Dict[str, Any]:
    """HEAD request for an object — returns metadata; raises ClientError on 404."""
    return _s3().head_object(Bucket=get_settings().r2_bucket, Key=key)


def delete_object(key: str) -> None:
    """Delete an object by key. boto3's delete is idempotent on 404."""
    bucket = get_settings().r2_bucket
    _s3().delete_object(Bucket=bucket, Key=key)
    logger.info("R2 delete: r2://%s/%s", bucket, key)

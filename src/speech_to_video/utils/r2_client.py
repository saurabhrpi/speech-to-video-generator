"""Cloudflare R2 client (S3-compatible).

Two buckets currently in use:
- `R2_BUCKET` (default `speech-to-video-templates`) — public-read, served via custom
  domain `R2_PUBLIC_BASE_URL`. Long-TTL cache (1y immutable). For V2 template
  assets (driving videos, scene images, thumbnails).
- `R2_SELFIES_BUCKET` (default `speech-to-video-selfies`) — private. Selfies + Pipeline B
  intermediate composites. Server presigns short-TTL URLs when handing keys to providers.

All public functions accept an optional `bucket` parameter; when None, the templates
bucket is used. Pass `bucket=get_settings().r2_selfies_bucket` for selfies.

boto3 client is lazy-init from R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY.
Calls raise R2NotConfigured if any of those are unset.
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


def _resolve_bucket(bucket: Optional[str]) -> str:
    return bucket or get_settings().r2_bucket


def public_url(key: str) -> str:
    """Public URL for a key under the templates-bucket custom domain.
    Only meaningful for the public-read templates bucket; not for selfies (private)."""
    base = get_settings().r2_public_base_url.rstrip("/")
    return f"{base}/{key.lstrip('/')}"


def upload_file(
    local_path: str,
    key: str,
    content_type: Optional[str] = None,
    cache_control: str = DEFAULT_CACHE_CONTROL,
    bucket: Optional[str] = None,
) -> str:
    """Upload a local file. Returns the public URL (only meaningful for templates bucket)."""
    if content_type is None:
        guessed, _ = mimetypes.guess_type(local_path)
        content_type = guessed or "application/octet-stream"
    extra = {"CacheControl": cache_control, "ContentType": content_type}
    target_bucket = _resolve_bucket(bucket)
    _s3().upload_file(local_path, target_bucket, key, ExtraArgs=extra)
    logger.info(
        "R2 upload: %s -> r2://%s/%s (%s)",
        os.path.basename(local_path), target_bucket, key, content_type,
    )
    return public_url(key)


def download_to_path(key: str, local_path: str, bucket: Optional[str] = None) -> str:
    """Download an R2 object to a local file. Returns the local path."""
    target_bucket = _resolve_bucket(bucket)
    _s3().download_file(target_bucket, key, local_path)
    logger.info("R2 download: r2://%s/%s -> %s", target_bucket, key, local_path)
    return local_path


def download_to_bytes(key: str, bucket: Optional[str] = None) -> bytes:
    """Fetch an R2 object's body as bytes."""
    target_bucket = _resolve_bucket(bucket)
    resp = _s3().get_object(Bucket=target_bucket, Key=key)
    return resp["Body"].read()


def generate_presigned_get_url(
    key: str,
    bucket: Optional[str] = None,
    expires_in: int = 600,
) -> str:
    """Generate a short-TTL presigned GET URL. Use for handing private-bucket keys
    (e.g. selfies, composites) to upstream providers (Kling, Vertex)."""
    target_bucket = _resolve_bucket(bucket)
    return _s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": target_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def head_object(key: str, bucket: Optional[str] = None) -> Dict[str, Any]:
    """HEAD request for an object — returns metadata; raises ClientError on 404."""
    return _s3().head_object(Bucket=_resolve_bucket(bucket), Key=key)


def delete_object(key: str, bucket: Optional[str] = None) -> None:
    """Delete an object by key. boto3's delete is idempotent on 404."""
    target_bucket = _resolve_bucket(bucket)
    _s3().delete_object(Bucket=target_bucket, Key=key)
    logger.info("R2 delete: r2://%s/%s", target_bucket, key)


def upload_bytes(
    data: bytes,
    key: str,
    content_type: str,
    bucket: Optional[str] = None,
    cache_control: str = DEFAULT_CACHE_CONTROL,
) -> str:
    """Upload an in-memory byte buffer (no temp file). Returns the public URL
    (only meaningful for the templates bucket; private buckets ignore it)."""
    target_bucket = _resolve_bucket(bucket)
    _s3().put_object(
        Bucket=target_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl=cache_control,
    )
    logger.info("R2 put_object: r2://%s/%s (%d bytes, %s)", target_bucket, key, len(data), content_type)
    return public_url(key)


def list_objects(prefix: str, bucket: Optional[str] = None) -> list:
    """List all objects under `prefix`. Handles pagination internally.
    Returns list of dicts: [{Key, Size, LastModified, ETag}, ...]"""
    target_bucket = _resolve_bucket(bucket)
    paginator = _s3().get_paginator("list_objects_v2")
    out = []
    for page in paginator.paginate(Bucket=target_bucket, Prefix=prefix):
        out.extend(page.get("Contents") or [])
    return out


def delete_prefix(prefix: str, bucket: Optional[str] = None) -> int:
    """Delete every object under `prefix`. Returns count of objects deleted.
    Uses S3 batched delete (up to 1000 keys per request)."""
    target_bucket = _resolve_bucket(bucket)
    s3 = _s3()
    paginator = s3.get_paginator("list_objects_v2")
    total = 0
    for page in paginator.paginate(Bucket=target_bucket, Prefix=prefix):
        contents = page.get("Contents") or []
        if not contents:
            continue
        # S3 DeleteObjects accepts up to 1000 keys per call; one ListObjects page
        # is also capped at 1000, so one delete per page is fine.
        objects = [{"Key": obj["Key"]} for obj in contents]
        s3.delete_objects(Bucket=target_bucket, Delete={"Objects": objects, "Quiet": True})
        total += len(objects)
    if total:
        logger.info("R2 delete_prefix: r2://%s/%s* (%d objects)", target_bucket, prefix, total)
    return total

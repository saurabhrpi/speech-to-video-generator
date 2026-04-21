"""Credits API — mobile calls this after a successful RevenueCat purchase.

Flow:
    1. Mobile completes an IAP via `Purchases.purchasePackage(pkg)`.
    2. Mobile calls POST /api/credits/grant with {product_id, transaction_id}.
    3. Server verifies the purchase by fetching the RC subscriber and
       confirming the transaction id is present under non_subscriptions.
    4. Server calls credit_store.grant(uid, PACK_CREDITS[product_id], tx_id).
       Grant is idempotent — replaying the same transaction_id is a no-op.

We hit the RevenueCat REST API (not a webhook) so there is no external
infra to maintain. REVENUECAT_REST_API_KEY must be the Secret REST key
from RC dashboard -> Project Settings -> API Keys (NOT the public SDK
keys used on mobile).
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..utils import credit_store
from ..utils.config import get_settings
from .firebase_auth import verify_firebase_token

logger = logging.getLogger(__name__)

router = APIRouter()

# Product-id -> credits granted per purchase. Must match the product ids
# configured in RevenueCat (Test Store or App Store) and the PACK_SKUS the
# mobile app uses to identify packages.
PACK_CREDITS: Dict[str, int] = {
    "pro_pack_50": 50,
    "pro_pack_120": 120,
    "pro_pack_250": 250,
}

_RC_BASE_URL = "https://api.revenuecat.com/v1"


def _rc_get_subscriber(uid: str, api_key: str) -> Dict:
    url = f"{_RC_BASE_URL}/subscribers/{uid}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as exc:
        logger.warning("RC REST unreachable: %s", exc)
        raise HTTPException(status_code=502, detail="revenuecat_unreachable")

    if resp.status_code == 401 or resp.status_code == 403:
        logger.error("RC REST auth rejected (status=%s)", resp.status_code)
        raise HTTPException(status_code=500, detail="revenuecat_auth_error")
    if resp.status_code == 404:
        # RC returns 404 when the user has never been seen. Treat as "no
        # purchase" rather than a hard server error.
        return {}
    if resp.status_code >= 400:
        logger.warning("RC REST returned %s: %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail=f"revenuecat_error_{resp.status_code}")

    try:
        return resp.json() or {}
    except ValueError:
        raise HTTPException(status_code=502, detail="revenuecat_bad_json")


def _verify_purchase(
    subscriber_payload: Dict,
    product_id: str,
    transaction_id: str,
) -> bool:
    """True iff the subscriber record contains a non-subscription purchase
    of `product_id` whose store transaction id matches `transaction_id`."""
    subscriber = subscriber_payload.get("subscriber") or {}
    non_subs = subscriber.get("non_subscriptions") or {}
    entries = non_subs.get(product_id) or []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        store_tx = entry.get("store_transaction_identifier")
        rc_id = entry.get("id")
        if transaction_id and (store_tx == transaction_id or rc_id == transaction_id):
            return True
    return False


@router.post("/api/credits/grant")
async def grant_credits(request: Request, user: Dict = Depends(verify_firebase_token)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")

    product_id = (body.get("product_id") or "").strip()
    transaction_id = (body.get("transaction_id") or "").strip()

    if not product_id:
        raise HTTPException(status_code=400, detail="product_id_required")
    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction_id_required")
    if product_id not in PACK_CREDITS:
        raise HTTPException(status_code=400, detail=f"unknown_product: {product_id}")

    settings = get_settings()
    api_key = (settings.revenuecat_rest_api_key or "").strip()
    if not api_key:
        logger.error("REVENUECAT_REST_API_KEY is not configured")
        raise HTTPException(status_code=500, detail="revenuecat_not_configured")

    uid = user["uid"]
    payload = _rc_get_subscriber(uid, api_key)
    if not _verify_purchase(payload, product_id, transaction_id):
        # RC may not have ingested the receipt yet — mobile can retry.
        logger.info(
            "RC verification failed uid=%s product=%s tx=%s",
            uid, product_id, transaction_id,
        )
        raise HTTPException(status_code=404, detail="purchase_not_found_yet")

    amount = PACK_CREDITS[product_id]
    result = credit_store.grant(uid=uid, amount=amount, tx_id=transaction_id)
    logger.info(
        "credits granted uid=%s product=%s amount=%s balance=%s already=%s",
        uid, product_id, result["granted"], result["balance"], result["already_applied"],
    )
    return JSONResponse(result)

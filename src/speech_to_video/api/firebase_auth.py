"""Firebase Bearer-token verification for FastAPI.

Mobile clients attach `Authorization: Bearer <firebase_id_token>` on every
request. `verify_firebase_token` is a FastAPI dependency that validates the
token with firebase-admin and returns `{uid, is_anonymous, email, name}`.

firebase-admin is initialized lazily on first call from one of two sources
(in priority order):
  1. `FIREBASE_SERVICE_ACCOUNT_JSON` — the full service-account JSON as a
     single-line string. Used on Replit / any cloud host.
  2. `FIREBASE_SERVICE_ACCOUNT_PATH` — a filesystem path to the JSON file.
     Used for local development.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

_initialized = False


def _init_firebase_admin() -> None:
    global _initialized
    if _initialized:
        return
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:
        _initialized = True
        return

    sa_json_raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if sa_json_raw:
        try:
            sa_dict = json.loads(sa_json_raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"FIREBASE_SERVICE_ACCOUNT_JSON is set but is not valid JSON: {exc}"
            ) from exc
        cred = credentials.Certificate(sa_dict)
        firebase_admin.initialize_app(cred)
        _initialized = True
        logger.info(
            "firebase-admin initialized from FIREBASE_SERVICE_ACCOUNT_JSON (project_id=%s)",
            sa_dict.get("project_id", "?"),
        )
        return

    sa_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    sa_path = os.path.expanduser(sa_path) if sa_path else ""
    if not sa_path or not os.path.isfile(sa_path):
        raise RuntimeError(
            "Firebase credentials not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON "
            "(preferred, full JSON string) or FIREBASE_SERVICE_ACCOUNT_PATH (path to "
            f"JSON file). Path got: {sa_path!r}"
        )
    cred = credentials.Certificate(sa_path)
    firebase_admin.initialize_app(cred)
    _initialized = True
    logger.info("firebase-admin initialized from FIREBASE_SERVICE_ACCOUNT_PATH=%s", sa_path)


def _decode_token(id_token: str) -> Dict:
    from firebase_admin import auth as fb_auth

    _init_firebase_admin()
    try:
        return fb_auth.verify_id_token(id_token)
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="token_expired")
    except fb_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="token_revoked")
    except fb_auth.InvalidIdTokenError as exc:
        raise HTTPException(status_code=401, detail=f"invalid_token: {exc}")
    except Exception as exc:
        logger.warning("firebase token verify failed: %s", exc)
        raise HTTPException(status_code=401, detail="invalid_token")


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="missing_authorization")
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="invalid_authorization_header")
    return parts[1].strip()


def _user_from_claims(claims: Dict) -> Dict:
    provider = (claims.get("firebase") or {}).get("sign_in_provider") or ""
    is_anonymous = provider == "anonymous"
    return {
        "uid": claims["uid"],
        "is_anonymous": is_anonymous,
        "email": claims.get("email"),
        "name": claims.get("name"),
        "provider": provider,
    }


def verify_firebase_token(authorization: Optional[str] = Header(default=None)) -> Dict:
    """FastAPI dep: require a valid Firebase ID token. Returns user dict."""
    token = _extract_token(authorization)
    claims = _decode_token(token)
    return _user_from_claims(claims)

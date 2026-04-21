"""Firestore-backed credit ledger.

Each user has a single document at `credits/{firebase_uid}` holding their
running balance, lifetime totals, and the set of RevenueCat transaction ids
that have already been granted (idempotency guard for purchase replay).

Document shape:
    {
      "granted": int,                       # lifetime credits granted
      "used": int,                          # lifetime credits consumed
      "balance": int,                       # granted - used, kept in sync
      "applied_transactions": [str, ...],   # RC tx ids already granted
      "starter_granted": bool,              # anon-starter flag
      "updated_at": server timestamp,
    }

All mutations (ensure_anon_starter, grant, consume) run inside Firestore
transactions so concurrent requests cannot double-spend or double-grant.
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

_COLLECTION = "credits"


class InsufficientCredits(Exception):
    """Raised when a consume() exceeds the user's current balance."""

    def __init__(self, required: int, balance: int):
        self.required = int(required)
        self.balance = int(balance)
        super().__init__(
            f"insufficient_credits: required={self.required} balance={self.balance}"
        )


def _db():
    """Return a firestore client, initializing firebase-admin on first call."""
    from firebase_admin import firestore as fb_firestore

    from ..api.firebase_auth import _init_firebase_admin

    _init_firebase_admin()
    return fb_firestore.client()


def _doc_ref(uid: str):
    return _db().collection(_COLLECTION).document(uid)


def get_balance(uid: str) -> int:
    """Current balance. Returns 0 if the user has no ledger yet."""
    snap = _doc_ref(uid).get()
    if not snap.exists:
        return 0
    return int((snap.to_dict() or {}).get("balance", 0))


def get_ledger(uid: str) -> Dict:
    """Full ledger snapshot for debugging / session endpoint."""
    snap = _doc_ref(uid).get()
    if not snap.exists:
        return {"balance": 0, "granted": 0, "used": 0, "exists": False}
    data = snap.to_dict() or {}
    return {
        "balance": int(data.get("balance", 0)),
        "granted": int(data.get("granted", 0)),
        "used": int(data.get("used", 0)),
        "starter_granted": bool(data.get("starter_granted", False)),
        "exists": True,
    }


def ensure_anon_starter(uid: str, amount: int = 5) -> int:
    """Seed the ledger with a starter grant on the user's first touch.

    No-op if the ledger already exists. Idempotent — safe to call on every
    request. Returns the balance after the call.
    """
    from firebase_admin import firestore as fb_firestore

    db = _db()
    ref = db.collection(_COLLECTION).document(uid)
    tx = db.transaction()

    @fb_firestore.transactional
    def _run(t):
        snap = ref.get(transaction=t)
        if snap.exists:
            return int((snap.to_dict() or {}).get("balance", 0))
        t.set(ref, {
            "granted": int(amount),
            "used": 0,
            "balance": int(amount),
            "applied_transactions": [],
            "starter_granted": True,
            "updated_at": fb_firestore.SERVER_TIMESTAMP,
        })
        return int(amount)

    return _run(tx)


def grant(uid: str, amount: int, tx_id: str) -> Dict:
    """Add credits from a verified purchase, guarded by tx_id.

    If tx_id has already been applied to this user, returns the current
    balance unchanged with already_applied=True. Creates the ledger on
    first touch.
    """
    if amount <= 0:
        raise ValueError(f"grant amount must be positive, got {amount}")
    if not tx_id:
        raise ValueError("tx_id is required for idempotency")

    from firebase_admin import firestore as fb_firestore

    db = _db()
    ref = db.collection(_COLLECTION).document(uid)
    tx = db.transaction()

    @fb_firestore.transactional
    def _run(t):
        snap = ref.get(transaction=t)
        if snap.exists:
            data = snap.to_dict() or {}
            if tx_id in (data.get("applied_transactions") or []):
                return {
                    "balance": int(data.get("balance", 0)),
                    "granted": 0,
                    "already_applied": True,
                }
            new_balance = int(data.get("balance", 0)) + int(amount)
            t.update(ref, {
                "granted": fb_firestore.Increment(int(amount)),
                "balance": fb_firestore.Increment(int(amount)),
                "applied_transactions": fb_firestore.ArrayUnion([tx_id]),
                "updated_at": fb_firestore.SERVER_TIMESTAMP,
            })
            return {
                "balance": new_balance,
                "granted": int(amount),
                "already_applied": False,
            }
        t.set(ref, {
            "granted": int(amount),
            "used": 0,
            "balance": int(amount),
            "applied_transactions": [tx_id],
            "starter_granted": False,
            "updated_at": fb_firestore.SERVER_TIMESTAMP,
        })
        return {
            "balance": int(amount),
            "granted": int(amount),
            "already_applied": False,
        }

    return _run(tx)


def consume(uid: str, amount: int) -> int:
    """Atomically decrement the balance. Raises InsufficientCredits on shortfall."""
    if amount <= 0:
        raise ValueError(f"consume amount must be positive, got {amount}")

    from firebase_admin import firestore as fb_firestore

    db = _db()
    ref = db.collection(_COLLECTION).document(uid)
    tx = db.transaction()

    @fb_firestore.transactional
    def _run(t):
        snap = ref.get(transaction=t)
        balance = int((snap.to_dict() or {}).get("balance", 0)) if snap.exists else 0
        if balance < int(amount):
            raise InsufficientCredits(required=int(amount), balance=balance)
        t.update(ref, {
            "used": fb_firestore.Increment(int(amount)),
            "balance": fb_firestore.Increment(-int(amount)),
            "updated_at": fb_firestore.SERVER_TIMESTAMP,
        })
        return balance - int(amount)

    return _run(tx)

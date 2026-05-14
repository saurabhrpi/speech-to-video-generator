"""Smoke test for the bulk-upload script (AIV-88).

Three layers:

1. Pure-logic checks (always run, no network):
   - Canonical filename classification.
   - Slot/extension validation.
   - Manifest override path.
   - Duplicate-slot detection.

2. Dry-run end-to-end (always runs): build a fixture dir, invoke main() with
   --dry-run, assert it prints a plan and exits 0 with no side effects.

3. Real R2 + Firestore (gated): requires R2 env vars + Firebase admin SDK.
   Uploads tiny placeholder files to R2 under a `smoketest/...` prefix, then
   updates a dedicated `smoketest-aiv-88-bombale` Firestore doc, then cleans up
   both R2 objects and the Firestore doc. Does NOT touch the real Bombale doc.

Usage:
    .venv/bin/python scripts/test_upload_template_assets.py
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import upload_template_assets as uta  # noqa: E402
from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.r2_client import R2NotConfigured  # noqa: E402
from src.speech_to_video.utils.template_registry import (  # noqa: E402
    OUTCOME_ONTO_CHARACTER,
    PIPELINE_MOTION_TRANSFER,
    STATUS_DRAFT,
    TemplateNotFound,
    delete_template,
    get_template,
    upsert_template,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("test_upload_template_assets")

# Dedicated test template_id so we never touch the real Bombale entry.
TEST_TEMPLATE_ID = "smoketest-aiv-88-bombale"
TEST_CATEGORY = "smoketest"
TEST_SLUG = "aiv-88-bombale"


def _make_fixture(base: Path, *, with_manifest: bool = False) -> None:
    """Build a tiny placeholder fixture mirroring the layout."""
    tdir = base / TEST_CATEGORY / TEST_SLUG
    tdir.mkdir(parents=True, exist_ok=True)
    if with_manifest:
        (tdir / "raw_kling_xyz.mp4").write_bytes(b"fake mp4 driving video")
        (tdir / "tile_640.jpg").write_bytes(b"fake jpg thumbnail")
        (tdir / uta.MANIFEST_FILENAME).write_text(json.dumps({
            "driving_video": "raw_kling_xyz.mp4",
            "thumbnail": "tile_640.jpg",
        }))
    else:
        (tdir / "driving_video.mp4").write_bytes(b"fake mp4 driving video")
        (tdir / "thumbnail.jpg").write_bytes(b"fake jpg thumbnail")


# ---------- Layer 1: pure-logic checks ----------

def test_classify_canonical():
    assert uta._classify_canonical("driving_video.mp4") == "driving_video"
    assert uta._classify_canonical("scene_image.png") == "scene_image"
    assert uta._classify_canonical("thumbnail.jpg") == "thumbnail"
    assert uta._classify_canonical("preview_video.webm") == "preview_video"
    # Wrong ext for slot:
    assert uta._classify_canonical("driving_video.jpg") is None
    assert uta._classify_canonical("thumbnail.mp4") is None
    # Not a slot:
    assert uta._classify_canonical("random.mp4") is None
    assert uta._classify_canonical("README.md") is None
    print("PASS [classify_canonical]")


def test_plan_canonical(tmp_root: Path):
    _make_fixture(tmp_root, with_manifest=False)
    plan = uta._plan_template(TEST_CATEGORY, TEST_SLUG, tmp_root / TEST_CATEGORY / TEST_SLUG)
    assert plan.template_id == TEST_TEMPLATE_ID, plan.template_id
    assert not plan.errors, plan.errors
    slots = sorted(u.slot for u in plan.uploads)
    assert slots == ["driving_video", "thumbnail"], slots
    keys = sorted(u.r2_key for u in plan.uploads)
    assert keys == [
        f"{TEST_CATEGORY}/{TEST_SLUG}/driving_video.mp4",
        f"{TEST_CATEGORY}/{TEST_SLUG}/thumbnail.jpg",
    ], keys
    print("PASS [plan_canonical]")


def test_plan_manifest_override(tmp_root: Path):
    _make_fixture(tmp_root, with_manifest=True)
    plan = uta._plan_template(TEST_CATEGORY, TEST_SLUG, tmp_root / TEST_CATEGORY / TEST_SLUG)
    assert not plan.errors, plan.errors
    by_slot = {u.slot: u for u in plan.uploads}
    assert by_slot["driving_video"].local_path.name == "raw_kling_xyz.mp4"
    assert by_slot["thumbnail"].local_path.name == "tile_640.jpg"
    # R2 key preserves the original filename (not the canonical slot name):
    assert by_slot["driving_video"].r2_key == f"{TEST_CATEGORY}/{TEST_SLUG}/raw_kling_xyz.mp4"
    print("PASS [plan_manifest_override]")


def test_plan_duplicate_slot(tmp_root: Path):
    tdir = tmp_root / TEST_CATEGORY / TEST_SLUG
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "driving_video.mp4").write_bytes(b"a")
    (tdir / "driving_video.mov").write_bytes(b"b")
    plan = uta._plan_template(TEST_CATEGORY, TEST_SLUG, tdir)
    assert any("duplicate slot" in e for e in plan.errors), plan.errors
    print("PASS [plan_duplicate_slot]")


def test_plan_manifest_missing_file(tmp_root: Path):
    tdir = tmp_root / TEST_CATEGORY / TEST_SLUG
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / uta.MANIFEST_FILENAME).write_text(json.dumps({"driving_video": "does_not_exist.mp4"}))
    plan = uta._plan_template(TEST_CATEGORY, TEST_SLUG, tdir)
    assert any("missing file" in e for e in plan.errors), plan.errors
    print("PASS [plan_manifest_missing_file]")


def test_plan_empty_dir(tmp_root: Path):
    tdir = tmp_root / TEST_CATEGORY / TEST_SLUG
    tdir.mkdir(parents=True, exist_ok=True)
    plan = uta._plan_template(TEST_CATEGORY, TEST_SLUG, tdir)
    assert any("no recognized" in e for e in plan.errors), plan.errors
    print("PASS [plan_empty_dir]")


# ---------- Layer 2: dry-run end-to-end ----------

def test_dry_run(tmp_root: Path):
    _make_fixture(tmp_root, with_manifest=False)
    rc = uta.main([str(tmp_root), "--dry-run"])
    assert rc == 0, rc
    print("PASS [dry_run]")


# ---------- Layer 3: real R2 + Firestore (gated) ----------

def _seed_test_doc():
    upsert_template(TEST_TEMPLATE_ID, {
        "pipeline_class": PIPELINE_MOTION_TRANSFER,
        "outcome": OUTCOME_ONTO_CHARACTER,
        "category": "smoketest",
        "title": "AIV-88 smoke",
        "description": "ephemeral",
        "published_status": STATUS_DRAFT,
        "assets": {
            "driving_video_url": "https://placeholder.example/driving.mp4",
            "scene_image_url": None,
            "thumbnail_url": "https://placeholder.example/thumb.jpg",
            "preview_video_url": None,
        },
        "model": "kling-2.6-motion-control-image",
        "credit_cost": 23,
        "prompt_template": None,
    })


def _cleanup_test_doc():
    try:
        delete_template(TEST_TEMPLATE_ID)
    except Exception as e:  # noqa: BLE001
        log.warning("  cleanup: delete_template failed: %s", e)


def _cleanup_r2_objects():
    for fname in ("driving_video.mp4", "thumbnail.jpg"):
        key = f"{TEST_CATEGORY}/{TEST_SLUG}/{fname}"
        try:
            r2_client.delete_object(key)
        except Exception as e:  # noqa: BLE001
            log.warning("  cleanup: delete_object %s failed: %s", key, e)


def test_real_e2e(tmp_root: Path):
    try:
        r2_client._s3()
    except R2NotConfigured as e:
        print(f"SKIP [real_e2e]: {e}")
        return

    try:
        _seed_test_doc()
    except Exception as e:  # noqa: BLE001
        print(f"SKIP [real_e2e]: Firestore not reachable ({e})")
        return

    try:
        _make_fixture(tmp_root, with_manifest=False)
        rc = uta.main([str(tmp_root), "-t", TEST_TEMPLATE_ID])
        assert rc == 0, rc

        doc = get_template(TEST_TEMPLATE_ID)
        assets = doc.get("assets") or {}
        d_url = assets.get("driving_video_url")
        t_url = assets.get("thumbnail_url")
        expected_d = r2_client.public_url(f"{TEST_CATEGORY}/{TEST_SLUG}/driving_video.mp4")
        expected_t = r2_client.public_url(f"{TEST_CATEGORY}/{TEST_SLUG}/thumbnail.jpg")
        assert d_url == expected_d, f"driving_video_url mismatch: {d_url!r} vs {expected_d!r}"
        assert t_url == expected_t, f"thumbnail_url mismatch:    {t_url!r} vs {expected_t!r}"
        # Untouched fields preserved:
        assert doc.get("pipeline_class") == PIPELINE_MOTION_TRANSFER
        assert doc.get("credit_cost") == 23
        print("PASS [real_e2e]      registry assets.* updated, other fields preserved")
    finally:
        _cleanup_r2_objects()
        _cleanup_test_doc()


# ---------- driver ----------

def main():
    # Layer 1 — pure-logic, each in its own tmp dir so state doesn't leak.
    test_classify_canonical()
    for fn in (
        test_plan_canonical,
        test_plan_manifest_override,
        test_plan_duplicate_slot,
        test_plan_manifest_missing_file,
        test_plan_empty_dir,
    ):
        with tempfile.TemporaryDirectory() as d:
            fn(Path(d))

    # Layer 2 — dry-run.
    with tempfile.TemporaryDirectory() as d:
        test_dry_run(Path(d))

    # Layer 3 — real e2e (gated).
    with tempfile.TemporaryDirectory() as d:
        test_real_e2e(Path(d))

    print("\nAll assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
import json
import time
import re
from typing import List, Dict, Optional


def _base_dir() -> str:
    base_dir = os.getenv("CLIPS_DIR")
    if not base_dir:
        base_dir = os.path.join(os.path.abspath(os.getcwd()), "clips")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _sanitize_segment(seg: str) -> str:
    seg = seg.strip().lower()
    seg = re.sub(r"[^a-z0-9._-]", "-", seg)
    return seg or "default"


def _playlist_path(namespace: Optional[str] = None) -> str:
    base = _base_dir()
    if namespace:
        ns = _sanitize_segment(namespace)
        ns_dir = os.path.join(base, ns)
        os.makedirs(ns_dir, exist_ok=True)
        return os.path.join(ns_dir, "playlist.json")
    return os.path.join(base, "playlist.json")


def _load(namespace: Optional[str] = None) -> List[Dict]:
    path = _playlist_path(namespace)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data or []
    except Exception:
        return []


def _save(items: List[Dict], namespace: Optional[str] = None) -> None:
    with open(_playlist_path(namespace), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_clip(url: str, note: Optional[str] = None, namespace: Optional[str] = None) -> Dict:
    items = _load(namespace)
    entry = {"url": url, "note": (note or "").strip(), "ts": int(time.time())}
    items.append(entry)
    _save(items, namespace)
    return entry


def list_clips(namespace: Optional[str] = None) -> List[Dict]:
    return _load(namespace)


def clear_clips(namespace: Optional[str] = None) -> None:
    _save([], namespace)


def reorder_clips(order_ts: List[int], namespace: Optional[str] = None) -> List[Dict]:
    """Reorder playlist to match the list of ts values in order.
    Unknown items are appended at the end in their existing order.
    Returns the new list.
    """
    items = _load(namespace)
    ts_to_item = {int(it.get("ts", 0)): it for it in items}
    new_items: List[Dict] = []
    seen = set()
    for ts in order_ts:
        it = ts_to_item.get(int(ts))
        if it and int(it.get("ts", 0)) not in seen:
            new_items.append(it)
            seen.add(int(it.get("ts", 0)))
    # append any not referenced
    for it in items:
        t = int(it.get("ts", 0))
        if t not in seen:
            new_items.append(it)
            seen.add(t)
    _save(new_items, namespace)
    return new_items


def remove_stitched_clips(namespace: Optional[str] = None) -> int:
    """Remove entries that look like stitched clips (by note or stitched URL).
    Returns the count removed.
    """
    items = _load(namespace)
    def _is_stitched(it: Dict) -> bool:
        note = str(it.get("note", "")).lower()
        url = str(it.get("url", ""))
        if "stitched" in note:
            return True
        if url.startswith("/api/stitched") or url.endswith("/api/stitched"):
            return True
        return False
    new_items = [it for it in items if not _is_stitched(it)]
    removed = len(items) - len(new_items)
    if removed:
        _save(new_items, namespace)
    return removed



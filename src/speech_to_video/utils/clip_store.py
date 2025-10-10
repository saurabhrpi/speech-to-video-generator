import os
import json
import time
from typing import List, Dict, Optional


def _playlist_path() -> str:
    base = os.path.abspath(os.getcwd())
    clips_dir = os.path.join(base, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    return os.path.join(clips_dir, "playlist.json")


def _load() -> List[Dict]:
    path = _playlist_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data or []
    except Exception:
        return []


def _save(items: List[Dict]) -> None:
    with open(_playlist_path(), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_clip(url: str, note: Optional[str] = None) -> Dict:
    items = _load()
    entry = {"url": url, "note": (note or "").strip(), "ts": int(time.time())}
    items.append(entry)
    _save(items)
    return entry


def list_clips() -> List[Dict]:
    return _load()


def clear_clips() -> None:
    _save([])



from __future__ import annotations

import json
import re
from pathlib import Path

OUTPUT_ROOT = Path("output")


def _safe_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    return name or "item"


def save_json(subdir: str, name: str, data) -> Path:
    out_dir = OUTPUT_ROOT / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_safe_name(name)}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def save_raw(subdir: str, name: str, content: str, ext: str = "html") -> Path:
    out_dir = OUTPUT_ROOT / subdir / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_safe_name(name)}.{ext}"
    out_path.write_text(content, encoding="utf-8")
    return out_path

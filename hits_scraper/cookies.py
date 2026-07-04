"""Load a browser-exported session into a plain {name: value} dict.

Supports two common export formats:

1. Netscape "cookies.txt" (tab-separated), produced by extensions like
   "Get cookies.txt LOCALLY":
       .code.hits.university	TRUE	/	TRUE	1750000000	session	abc123

2. JSON list of cookie objects, produced by extensions like "Cookie-Editor"
   or "EditThisCookie":
       [{"name": "session", "value": "abc123", "domain": "...", ...}, ...]

3. Plain JSON object mapping name -> value:
       {"session": "abc123", "csrftoken": "def456"}
"""
from __future__ import annotations

import json
from pathlib import Path


def load_cookies(path: str | Path) -> dict[str, str]:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError(f"Cookie file {path} is empty")

    if text.lstrip().startswith(("[", "{")):
        return _load_json(text)
    return _load_netscape(text)


def _load_json(text: str) -> dict[str, str]:
    data = json.loads(text)
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    if isinstance(data, list):
        cookies = {}
        for item in data:
            name = item.get("name")
            value = item.get("value")
            if name is not None and value is not None:
                cookies[name] = value
        return cookies
    raise ValueError("Unrecognized JSON cookie format")


def _load_netscape(text: str) -> dict[str, str]:
    cookies = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        _domain, _flag, _path, _secure, _expiry, name, value = parts[:7]
        cookies[name] = value
    if not cookies:
        raise ValueError("No cookies parsed - check the file format")
    return cookies

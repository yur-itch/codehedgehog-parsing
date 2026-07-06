"""Load a browser-exported session into a list of domain-scoped cookies.

The site is split across subdomains (code.hits.university,
class.code.hits.university, user.code.hits.university, ...) that all read
the same session cookie(s), scoped with a leading-dot domain like
".hits.university" or ".code.hits.university". A flat {name: value} dict
loses that scoping and breaks auth on the API subdomains, so we keep
(name, value, domain, path) tuples and build a domain-aware httpx.Cookies
jar in client.py.

Supports two common export formats:

1. Netscape "cookies.txt" (tab-separated), produced by extensions like
   "Get cookies.txt LOCALLY":
       .code.hits.university	TRUE	/	TRUE	1750000000	session	abc123

2. JSON list of cookie objects, produced by extensions like "Cookie-Editor"
   or "EditThisCookie":
       [{"name": "session", "value": "abc123", "domain": "...", ...}, ...]

3. Plain JSON object mapping name -> value (no domain info - applied
   everywhere as a fallback):
       {"session": "abc123", "csrftoken": "def456"}
"""
from __future__ import annotations

import json
from pathlib import Path

Cookie = tuple[str, str, str, str]  # name, value, domain, path


def load_cookies(path: str | Path) -> list[Cookie]:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError(f"Cookie file {path} is empty")

    if text.lstrip().startswith(("[", "{")):
        return _load_json(text)
    return _load_netscape(text)


def _load_json(text: str) -> list[Cookie]:
    data = json.loads(text)
    if isinstance(data, dict):
        return [(str(k), str(v), "", "/") for k, v in data.items()]
    if isinstance(data, list):
        cookies = []
        for item in data:
            name = item.get("name")
            value = item.get("value")
            if name is not None and value is not None:
                domain = item.get("domain") or ""
                path = item.get("path") or "/"
                cookies.append((str(name), str(value), str(domain), str(path)))
        return cookies
    raise ValueError("Unrecognized JSON cookie format")


def _load_netscape(text: str) -> list[Cookie]:
    cookies = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _flag, path, _secure, _expiry, name, value = parts[:7]
        cookies.append((name, value, domain, path or "/"))
    if not cookies:
        raise ValueError("No cookies parsed - check the file format")
    return cookies

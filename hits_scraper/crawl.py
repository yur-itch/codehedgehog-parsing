"""BFS crawler that turns "clicking around the site" into a graph.

Nodes are distinct pieces of content (pages/routes the crawler visited),
identified by their normalized URL. Edges are the network requests that
were observed while arriving at a node, labeled with where the crawler
came from.

Safety model (this assumes navigation is side-effect free, per the
project's working assumption - it does NOT re-verify that):
  - only follows <a href> links, never clicks buttons or submits forms
  - only ever issues GET navigations itself
  - skips any link whose URL or visible text matches DENYLIST_KEYWORDS
    (logout, delete, drop, reset, unsubscribe, ...) as a belt-and-braces
    guard against accidentally triggering something destructive
  - stays same-origin
  - polite by default: small delay between page loads, single-threaded,
    hard cap on total pages via --max-pages
"""
from __future__ import annotations

import argparse
import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from playwright.sync_api import sync_playwright

from .cookies import load_cookies
from .config import BASE_URL

DENYLIST_KEYWORDS = re.compile(
    r"(log[\s_-]?out|sign[\s_-]?out|delete|remove|drop|reset|"
    r"unsubscribe|deactivat|revoke|\bban\b)",
    re.IGNORECASE,
)

SEED = "__seed__"


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = urlencode(sorted(parse_qsl(parsed.query)))
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", query, ""))


def is_denylisted(url: str, text: str = "") -> bool:
    return bool(DENYLIST_KEYWORDS.search(url) or DENYLIST_KEYWORDS.search(text or ""))


def cookies_to_playwright(cookie_path: str, base_url: str) -> list[dict]:
    raw = load_cookies(cookie_path)
    host = urlparse(base_url).hostname
    return [{"name": n, "value": v, "domain": host, "path": "/"} for n, v in raw.items()]


def crawl(
    seed_urls: list[str],
    cookie_path: str,
    max_pages: int = 200,
    delay: float = 0.4,
    headless: bool = True,
    timeout_ms: int = 20000,
) -> dict:
    origin_host = urlparse(BASE_URL).hostname

    nodes: dict[str, dict] = {}
    edge_map: dict[tuple[str, str], dict] = {}
    visited: set[str] = set()
    queue: deque[tuple[str, str]] = deque((SEED, u) for u in seed_urls)

    def add_edge(src: str, dst: str, requests: list[dict]):
        key = (src, dst)
        if key not in edge_map:
            edge_map[key] = {"from": src, "to": dst, "requests": []}
        edge_map[key]["requests"].extend(requests)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        context.add_cookies(cookies_to_playwright(cookie_path, BASE_URL))
        page = context.new_page()

        while queue and len(visited) < max_pages:
            src, url = queue.popleft()
            norm = normalize_url(url)

            if norm in visited:
                if src != norm:
                    add_edge(src, norm, [])
                continue
            visited.add(norm)

            captured: list[dict] = []

            def on_response(resp, _captured=captured):
                req = resp.request
                if req.resource_type in ("xhr", "fetch", "document"):
                    _captured.append(
                        {
                            "method": req.method,
                            "url": resp.url,
                            "status": resp.status,
                            "resource_type": req.resource_type,
                        }
                    )

            page.on("response", on_response)
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                title = page.title()
                nodes[norm] = {"id": norm, "url": norm, "title": title, "error": False}
            except Exception as e:
                nodes[norm] = {"id": norm, "url": norm, "title": f"ERROR: {e}", "error": True}
            finally:
                page.remove_listener("response", on_response)

            add_edge(src, norm, captured)

            if not nodes[norm]["error"]:
                try:
                    links = page.eval_on_selector_all(
                        "a[href]",
                        "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim()}))",
                    )
                except Exception:
                    links = []
                for link in links:
                    href = link.get("href", "")
                    text = link.get("text", "")
                    if not href or urlparse(href).hostname != origin_host:
                        continue
                    if is_denylisted(href, text):
                        continue
                    n2 = normalize_url(href)
                    if n2 not in visited:
                        queue.append((norm, href))

            time.sleep(delay)

        browser.close()

    return {
        "nodes": list(nodes.values()),
        "edges": list(edge_map.values()),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawl code.hits.university into a content graph")
    parser.add_argument("--cookies", default="cookies.txt")
    parser.add_argument("--seed", action="append", required=True, help="starting URL(s), repeatable")
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.4, help="seconds between page loads")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument("--out", default="output/graph.json")
    args = parser.parse_args()

    graph = crawl(
        args.seed,
        args.cookies,
        max_pages=args.max_pages,
        delay=args.delay,
        headless=not args.headed,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges -> {out_path}")


if __name__ == "__main__":
    main()

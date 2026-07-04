from __future__ import annotations

import httpx

from .config import BASE_URL, DEFAULT_HEADERS
from .cookies import load_cookies


def build_client(cookie_file: str) -> httpx.Client:
    cookies = load_cookies(cookie_file)
    client = httpx.Client(
        base_url=BASE_URL,
        cookies=cookies,
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=30.0,
    )
    return client


def check_auth(client: httpx.Client) -> bool:
    """Hits the site root and checks we weren't bounced to a login page.

    This is a coarse sanity check, not a real endpoint - refine once we
    know the actual "who am I" / profile endpoint.
    """
    resp = client.get("/")
    if resp.status_code >= 400:
        return False
    lowered = resp.text.lower()
    if "login" in resp.url.path.lower():
        return False
    return True

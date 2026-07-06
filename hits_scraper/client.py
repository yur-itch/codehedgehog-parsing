from __future__ import annotations

import httpx

from .config import BASE_URL, DEFAULT_HEADERS
from .cookies import load_cookies


def build_client(cookie_file: str) -> httpx.Client:
    """Builds an httpx.Client authenticated with the site's JWT.

    The site's own session cookie ("token") is scoped to code.hits.university
    only, but the real API lives on separate subdomains
    (class.code.hits.university, user.code.hits.university, ...) and expects
    the same JWT as an "Authorization: Bearer <token>" header instead of a
    cookie. So we pull the JWT out of the exported cookie file and send it
    as a header on every request, rather than relying on cookie-jar domain
    matching.
    """
    cookies = {name: value for name, value, _domain, _path in load_cookies(cookie_file)}
    token = cookies.get("token")
    if not token:
        raise ValueError(
            "No 'token' cookie found in the cookie file - export cookies "
            "again while logged into code.hits.university"
        )

    headers = dict(DEFAULT_HEADERS)
    headers["Authorization"] = f"Bearer {token}"

    client = httpx.Client(
        base_url=BASE_URL,
        headers=headers,
        follow_redirects=True,
        timeout=30.0,
    )
    return client


def check_auth(client: httpx.Client) -> bool:
    """Hits the "who am I" endpoint on the user API to confirm the JWT works."""
    resp = client.get("https://user.code.hits.university/api/v1/user/retrieve")
    return resp.status_code == 200

BASE_URL = "https://code.hits.university"

# TODO: fill in once real endpoints are known from a HAR capture.
# Likely something like f"{BASE_URL}/api/..." - update after inspecting
# the site's Network tab.
API_BASE = f"{BASE_URL}/api"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}

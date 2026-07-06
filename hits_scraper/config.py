BASE_URL = "https://code.hits.university"

# Real API lives on separate subdomains (discovered via crawl.py), each
# serving /api/v1/... - not under BASE_URL/api like originally guessed.
CLASS_API_BASE = "https://class.code.hits.university/api/v1"
USER_API_BASE = "https://user.code.hits.university/api/v1"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
}

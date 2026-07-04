# codehedgehog-parsing

Archive your own data (tasks, submission attempts, leaderboard, etc.) from
`code.hits.university` before the academic year ends and access is cut off.

## Why this runs on your machine, not here

This session's sandbox has no network access to `code.hits.university`
(blocked by the environment's egress policy), and the scraper needs your
authenticated session anyway. So: you run this script locally, in a place
where the site is reachable in your normal browser.

## Status

The site is a SPA — its content is loaded via API calls, not plain HTML.
The endpoint paths in `hits_scraper/endpoints.py` are **placeholders**
(`/api/tasks`, `/api/submissions/my`, `/api/leaderboard`) and almost
certainly wrong. Two ways to get this working for real:

1. **Fastest for you**: run `python -m hits_scraper.cli fetch <path>` with
   guesses and report back what works, or just open DevTools → Network tab
   while browsing the site and tell me the real request URLs + a sample of
   the JSON response for: task list, one task's detail, your submissions
   history, and the leaderboard.
2. **One-shot**: export a HAR file while logged in and browsing those same
   pages (Chrome/Firefox DevTools → Network tab → right click → "Save all
   as HAR"), and share it with me. A HAR contains full request/response
   bodies, so I can read off the real API shape directly. **The HAR
   includes your session cookie in request headers** — if you don't want to
   share that, redact the `Cookie`/`Authorization` header *values* first
   (keep the header names and URLs/bodies intact) before sending it my way.

Once I know the real endpoints, I'll fill in `hits_scraper/endpoints.py`
with proper crawlers (pagination, following links from task list to task
detail, etc.) instead of the current stubs.

## Setup

```bash
pip install -r requirements.txt
```

## 1. Export your session cookies

Log into `code.hits.university` in your normal browser, then export
cookies for that domain into a file the script can read. Either format
works:

- **Netscape `cookies.txt`**: use a browser extension such as
  "Get cookies.txt LOCALLY" (Chrome/Firefox), export for
  `code.hits.university`, save as `cookies.txt` in this directory.
- **JSON**: an extension like "Cookie-Editor" can export the domain's
  cookies as JSON (`[{"name": ..., "value": ..., ...}, ...]`) — save as
  `cookies.json`.

Either file is read by `hits_scraper/cookies.py`. **Never commit this
file** — it's already covered by `.gitignore`.

## 2. Sanity-check the cookies work

```bash
python -m hits_scraper.cli --cookies cookies.txt check
```

## 3. Explore / fetch

```bash
# probe a candidate API path
python -m hits_scraper.cli --cookies cookies.txt fetch /api/tasks

# once endpoints.py is filled in with real paths:
python -m hits_scraper.cli --cookies cookies.txt tasks
python -m hits_scraper.cli --cookies cookies.txt submissions
python -m hits_scraper.cli --cookies cookies.txt leaderboard
```

Results are written under `output/` (also gitignored — this is your
personal academic data, not something to push to a shared repo unless you
decide otherwise).

## Layout

```
hits_scraper/
  config.py     base URL, headers
  cookies.py    loads cookies.txt / cookies.json into a dict
  client.py     builds an authenticated httpx.Client
  endpoints.py  the actual scraping logic (placeholders for now)
  save.py       writes JSON / raw HTML under output/
  cli.py        command-line entry point
```

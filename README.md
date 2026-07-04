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
playwright install chromium   # only needed for the crawler (crawl.py)
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

## 4. Map the whole site as a graph (optional)

Instead of guessing endpoints one at a time, you can let a headless
browser click through every link it finds and record what it discovers.
`crawl.py` does a breadth-first crawl starting from whatever URL(s) you
give it: it loads each page with your session, records every XHR/fetch/
document request that fires while the page loads, then follows every
same-origin `<a href>` link it finds - building up a graph where **nodes
are distinct pages/content** and **edges are the requests** that produced
them (labeled with method + status, e.g. `GET 200`).

This assumes navigation has no side effects (per the working assumption
for this task). As a safety net, the crawler still: only ever issues GET
navigations itself, never clicks buttons or submits forms, stays
same-origin, and skips any link whose URL/text matches a denylist
(logout, delete, remove, drop, reset, unsubscribe, ...). Review
`DENYLIST_KEYWORDS` in `hits_scraper/crawl.py` and extend it if the site
uses different wording for destructive actions.

```bash
python -m hits_scraper.crawl \
  --cookies cookies.txt \
  --seed https://code.hits.university/ \
  --seed https://code.hits.university/tasks \
  --max-pages 300 \
  --delay 0.5
```

- `--seed` can be repeated for multiple starting points (e.g. dashboard,
  task list, leaderboard) so the crawl covers areas not linked from the
  homepage.
- `--delay` is the pause (seconds) between page loads - keep it polite,
  this hits a real site.
- `--max-pages` is a hard cap so a runaway pagination loop can't make it
  crawl forever.
- Add `--headed` to watch the browser while it works (useful for
  debugging login/cookie issues).

Output goes to `output/graph.json` (nodes + edges, each edge carrying the
list of requests observed). Then render it into a single offline HTML
file you can just open in a browser - no server, no CDN, no network
needed (the graph library is vendored in `hits_scraper/vendor/`):

```bash
python -m hits_scraper.render_graph --graph output/graph.json --out output/graph_view.html
```

Click any node in the graph to see which request(s) produced it and where
it was reached from.

**Known limitation**: this only follows real `<a href="...">` links. If
part of the SPA navigates via JS-only click handlers with no real `href`
(no URL change), the crawler won't discover it - tell me which
pages/actions those are and I'll add targeted handling.

## Layout

```
hits_scraper/
  config.py       base URL, headers
  cookies.py      loads cookies.txt / cookies.json into a dict
  client.py       builds an authenticated httpx.Client
  endpoints.py    the actual scraping logic (placeholders for now)
  save.py         writes JSON / raw HTML under output/
  cli.py          command-line entry point (check / fetch / tasks / submissions / leaderboard)
  crawl.py         Playwright BFS crawler -> output/graph.json (content graph)
  render_graph.py  turns graph.json into a self-contained offline HTML viewer
  vendor/          vendored cytoscape.js (MIT) for offline graph rendering
```

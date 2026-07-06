# codehedgehog-parsing

Archive your own data (classes, tasks, submission attempts and source
code) from `code.hits.university` before the academic year ends and
access is cut off.

## Status

Working end-to-end. The real API was mapped by crawling the
authenticated site (see "How the API was found" below), `endpoints.py`
uses the real paths, and `cli.py archive` pulls everything into
`output/`. `render_site.py` then turns that into an offline HTML site
styled after the original.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium   # only needed for crawl.py (optional, see below)
```

## 1. Export your session cookies

Log into `code.hits.university` in your normal browser, then export
cookies for that domain into a file the script can read.

- **Netscape `cookies.txt`**: use a browser extension such as
  "Get cookies.txt LOCALLY" (Chrome/Firefox), export for
  `code.hits.university`, save as `cookies.txt` in this directory.
- **JSON**: an extension like "Cookie-Editor" can export the domain's
  cookies as JSON (`[{"name": ..., "value": ..., ...}, ...]`) — save as
  `cookies.json`.

Either file is read by `hits_scraper/cookies.py`. **Never commit this
file** — it's already covered by `.gitignore`.

What actually matters is the `token` cookie: it's a short-lived JWT
(observed lifetime: well under an hour, possibly just minutes) that the
site's own frontend reads out of the cookie and resends as an
`Authorization: Bearer <token>` header when calling its API subdomains.
`client.py` does the same. Practically this means:

- Re-export `cookies.txt` right before you run `archive`, not way ahead
  of time — a stale token fails with a 401 partway through.
- `archive` saves data as it goes, so if the token expires mid-run
  you don't lose what was already fetched, you just re-export and
  re-run to pick up the rest.

## 2. Sanity-check the cookies work

```bash
python -m hits_scraper.cli --cookies cookies.txt check
```

## 3. Archive everything

```bash
python -m hits_scraper.cli --cookies cookies.txt archive
```

This fetches, in one pass:

- your user profile
- every class you're enrolled in
- every attempt you've made in each class (`solution/class/<id>/attempt/get`,
  paginated), which gives task ids/names/scores/verdicts directly
- the full statement for every distinct task you've touched
- public comments on every solution
- every submission's full source code and per-test checker results

Raw JSON lands under `output/` (gitignored — this is your personal
academic data, not something to push to a shared repo).

```
output/
  user/me.json
  classes/all_classes.json
  classes/<class_id>/my_attempts.json
  tasks/task_<task_id>.json
  solutions/<solution_id>/comments.json
  solutions/<solution_id>/submission_<submission_id>.json
```

You can also probe an arbitrary path while exploring:

```bash
python -m hits_scraper.cli --cookies cookies.txt fetch /some/path
```

## 4. Browse the archive offline

```bash
python -m hits_scraper.render_site
```

Renders `output/` into a self-contained static HTML site under
`output/site/` (dark sidebar/banner/tabs, loosely styled after
code.hits.university's own UI) — one page per class/task/submission,
with your source code and test results readable without touching the
network again. Open `output/site/index.html` directly, or serve it:

```bash
python -m http.server 8421 --directory output/site
```

(`.claude/launch.json` has this wired up as the `archive-site` preview
config if you're driving this from an editor that reads it.)

## How the API was found (optional, already done)

The site is a SPA — content loads via API calls on separate subdomains
(`class.code.hits.university`, `user.code.hits.university`), not under
`code.hits.university/api` as you might guess from the main URL. This
was discovered with a Playwright BFS crawler that logs in with your
session, loads pages, and records every request that fires - you
shouldn't need to re-run this unless the site adds new sections that
aren't reachable from the ones already mapped.

```bash
python -m hits_scraper.crawl \
  --cookies cookies.txt \
  --seed https://code.hits.university/ \
  --max-pages 300 \
  --delay 0.5
```

- `--seed` can be repeated for multiple starting points so the crawl
  covers areas not linked from the homepage.
- `--delay` is the pause (seconds) between page loads — keep it polite,
  this hits a real site.
- `--max-pages` is a hard cap so a runaway pagination loop can't make it
  crawl forever.
- Add `--headed` to watch the browser while it works.

Safety net baked into the crawler: it only ever issues GET navigations,
never clicks buttons or submits forms, stays same-origin, and skips any
link whose URL/text matches a denylist (logout, delete, remove, drop,
reset, unsubscribe, ...). Review `DENYLIST_KEYWORDS` in
`hits_scraper/crawl.py` if the site uses different wording for
destructive actions.

Output goes to `output/graph.json` (nodes = pages, edges = the
requests that produced them). Render it into a single offline,
clickable HTML graph (cytoscape.js is vendored in
`hits_scraper/vendor/` — no CDN, no network needed):

```bash
python -m hits_scraper.render_graph --graph output/graph.json --out output/graph_view.html
```

**Known limitation**: the crawler only follows real `<a href="...">`
links, so JS-only click handlers with no real `href` won't be
discovered this way.

## Layout

```
hits_scraper/
  config.py       base URL + real API subdomains (class./user.)
  cookies.py      loads cookies.txt / cookies.json (domain/path-aware)
  client.py       builds an httpx.Client authenticated with the JWT Bearer token
  endpoints.py    the real scraping logic (fetch_everything, etc.)
  save.py         writes JSON under output/
  cli.py          command-line entry point (check / fetch / archive)
  crawl.py         Playwright BFS crawler -> output/graph.json (content graph)
  render_graph.py  turns graph.json into a self-contained offline HTML viewer
  render_site.py   turns output/ into an offline HTML site styled after the original
  vendor/          vendored cytoscape.js (MIT) for offline graph rendering
```

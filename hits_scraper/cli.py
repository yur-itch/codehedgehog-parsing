from __future__ import annotations

import argparse
import sys

from . import endpoints, save
from .client import build_client, check_auth


def cmd_check(args):
    client = build_client(args.cookies)
    ok = check_auth(client)
    print("OK - looks authenticated" if ok else "FAILED - looks logged out, re-export cookies")
    sys.exit(0 if ok else 1)


def cmd_fetch(args):
    """Generic explorer: GET an arbitrary path and save/preview the response.

    Useful for probing candidate API paths before endpoints.py is filled in.
    """
    client = build_client(args.cookies)
    resp = client.get(args.path)
    print(f"GET {args.path} -> {resp.status_code} ({resp.headers.get('content-type')})")
    name = args.path.strip("/").replace("/", "_") or "root"
    ctype = resp.headers.get("content-type", "")
    if "json" in ctype:
        data = resp.json()
        out = save.save_json("explore", name, data)
        print(f"saved JSON to {out}")
    else:
        out = save.save_raw("explore", name, resp.text, ext="html")
        print(f"saved raw response to {out}")
    print("--- preview ---")
    print(resp.text[:1000])


def cmd_tasks(args):
    client = build_client(args.cookies)
    tasks = endpoints.fetch_tasks(client)
    print(f"fetched {len(tasks)} tasks")


def cmd_submissions(args):
    client = build_client(args.cookies)
    subs = endpoints.fetch_my_submissions(client)
    print(f"fetched {len(subs)} submissions")


def cmd_leaderboard(args):
    client = build_client(args.cookies)
    endpoints.fetch_leaderboard(client)
    print("fetched leaderboard")


def main():
    parser = argparse.ArgumentParser(description="code.hits.university scraper")
    parser.add_argument("--cookies", default="cookies.txt", help="path to exported cookie file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="verify the cookie file authenticates").set_defaults(func=cmd_check)

    p_fetch = sub.add_parser("fetch", help="GET an arbitrary path and save the response")
    p_fetch.add_argument("path", help="e.g. /api/tasks")
    p_fetch.set_defaults(func=cmd_fetch)

    sub.add_parser("tasks", help="fetch all tasks").set_defaults(func=cmd_tasks)
    sub.add_parser("submissions", help="fetch my submissions/attempts").set_defaults(func=cmd_submissions)
    sub.add_parser("leaderboard", help="fetch the leaderboard").set_defaults(func=cmd_leaderboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

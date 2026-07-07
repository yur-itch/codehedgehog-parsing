"""Real scraping logic for code.hits.university.

The site is a SPA split across API subdomains discovered by crawling the
authenticated site with hits_scraper.crawl (see output/graph.json) and
probing responses directly:

    class.code.hits.university/api/v1/...   classes, tasks, solutions
    user.code.hits.university/api/v1/...    current user profile

client.build_client() attaches the JWT ("token" cookie) as a Bearer
Authorization header - the actual "token" cookie is scoped only to
code.hits.university and isn't sent to these API subdomains by browsers'
normal cookie rules either, but the SPA reads it out of the cookie and
resends it as a header. That JWT is short-lived (observed ~minutes), so
fetch_everything() below saves raw JSON as it goes, and skips re-fetching
(and thus never overwrites) any per-item file already on disk - a re-run
after the token expires or access gets cut off entirely just resumes from
where it left off instead of redoing, or risking clobbering, work already
archived.

Key discovery: `solution/class/<classId>/attempt/get` (paginated,
filterable by sender_id) returns every attempt the user has made in that
class directly, including task_id/task_name/solution_id/scores/verdicts -
no need to walk classStudyModule -> classSection to discover tasks, since
class sections carry no task list of their own via the API.

Each attempt's "id" is also the submission id used by
`solution/<solutionId>/submission/<attemptId>/get`, which returns the full
checker output *and* the submitted source in `contents`.
"""
from __future__ import annotations

import httpx

from . import save
from .config import CLASS_API_BASE, USER_API_BASE


def _get(client: httpx.Client, url: str) -> dict:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()


def _paginate(client: httpx.Client, url_fmt: str, *, limit: int, items_key: str) -> list[dict]:
    """Follows page=1,2,... until fewer than `limit` items come back."""
    items: list[dict] = []
    page = 1
    while True:
        data = _get(client, url_fmt.format(page=page, limit=limit))
        batch = data.get(items_key, [])
        items.extend(batch)
        if len(batch) < limit:
            break
        page += 1
    return items


def fetch_current_user(client: httpx.Client) -> dict:
    data = _get(client, f"{USER_API_BASE}/user/retrieve")
    save.save_json("user", "me", data)
    return data["user"]


def fetch_classes(client: httpx.Client) -> list[dict]:
    """All classes ("courses") the current user is enrolled in."""
    classes = _paginate(
        client,
        f"{CLASS_API_BASE}/class/get?page={{page}}&limit={{limit}}",
        limit=50,
        items_key="classes",
    )
    save.save_json("classes", "all_classes", classes)
    return classes


def fetch_my_attempts_for_class(client: httpx.Client, class_id: str, user_id: str) -> list[dict]:
    """Every attempt the current user has made in this class (all tasks)."""
    attempts = _paginate(
        client,
        (
            f"{CLASS_API_BASE}/solution/class/{class_id}/attempt/get"
            f"?page={{page}}&limit={{limit}}&sender_id={user_id}"
        ),
        limit=100,
        items_key="attempts",
    )
    save.save_json(f"classes/{class_id}", "my_attempts", attempts)
    return attempts


def fetch_task_detail(client: httpx.Client, task_id: str) -> bool:
    """Fetches and saves a task's statement. Returns False (no request made)
    if it's already on disk - task statements are treated as immutable
    once archived, so re-runs never re-fetch (and can't overwrite) them.
    """
    if save.has_json("tasks", f"task_{task_id}"):
        return False
    data = _get(client, f"{CLASS_API_BASE}/classTask/{task_id}/get")
    save.save_json("tasks", f"task_{task_id}", data)
    return True


def fetch_solution_comments(client: httpx.Client, solution_id: str) -> bool:
    """Same skip-if-present behavior as fetch_task_detail."""
    if save.has_json(f"solutions/{solution_id}", "comments"):
        return False
    data = _get(client, f"{CLASS_API_BASE}/solution/{solution_id}/comment/public/get")
    save.save_json(f"solutions/{solution_id}", "comments", data)
    return True


def fetch_submission(client: httpx.Client, solution_id: str, submission_id: str) -> bool:
    """Same skip-if-present behavior as fetch_task_detail - a submission's
    source code and checker results never change after the fact.
    """
    if save.has_json(f"solutions/{solution_id}", f"submission_{submission_id}"):
        return False
    data = _get(
        client,
        f"{CLASS_API_BASE}/solution/{solution_id}/submission/{submission_id}/get",
    )
    save.save_json(f"solutions/{solution_id}", f"submission_{submission_id}", data)
    return True


def fetch_everything(client: httpx.Client) -> None:
    """One-pass archive of the current user's classes, tasks, attempts and
    submitted source code.

    Saves raw JSON under output/ as it goes (rather than only returning a
    big structure) so a JWT expiring partway through a slow run doesn't
    lose everything already fetched. Per-item files (task statements,
    solution comments, submission source+results) are skipped entirely if
    already on disk - they're treated as immutable, so a re-run after a
    token expired or access got cut off never re-fetches (and can't
    overwrite) data already archived; it only goes after what's missing.
    """
    me = fetch_current_user(client)
    user_id = me["id"]
    print(f"user: {me.get('name')} ({user_id})")

    classes = fetch_classes(client)
    print(f"{len(classes)} classes")

    seen_task_ids: set[str] = set()
    seen_solution_ids: set[str] = set()
    new_tasks = new_comments = new_submissions = 0
    failed = 0

    for cls in classes:
        class_id = cls["id"]
        print(f"class {class_id} - {cls.get('name')}")

        attempts = fetch_my_attempts_for_class(client, class_id, user_id)
        print(f"  {len(attempts)} attempts")

        for attempt in attempts:
            task_id = attempt.get("task_id")
            solution_id = attempt.get("solution_id")
            submission_id = attempt.get("id")

            if task_id and task_id not in seen_task_ids:
                seen_task_ids.add(task_id)
                try:
                    if fetch_task_detail(client, task_id):
                        new_tasks += 1
                except httpx.HTTPStatusError as exc:
                    failed += 1
                    print(f"  task {task_id} detail failed: {exc}")

            if solution_id and solution_id not in seen_solution_ids:
                seen_solution_ids.add(solution_id)
                try:
                    if fetch_solution_comments(client, solution_id):
                        new_comments += 1
                except httpx.HTTPStatusError:
                    pass

            if solution_id and submission_id:
                try:
                    if fetch_submission(client, solution_id, submission_id):
                        new_submissions += 1
                except httpx.HTTPStatusError as exc:
                    failed += 1
                    print(f"  submission {submission_id} failed: {exc}")

    print(
        f"done - {len(seen_task_ids)} tasks seen ({new_tasks} newly fetched), "
        f"{len(seen_solution_ids)} solutions seen ({new_submissions} submissions, "
        f"{new_comments} comment threads newly fetched)"
    )
    if failed:
        print(
            f"{failed} request(s) failed (likely the JWT expired mid-run) - "
            "re-export cookies.txt and re-run archive to pick up what's missing"
        )

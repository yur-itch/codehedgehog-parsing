"""Site-specific scraping logic.

Everything in this file is a placeholder. code.hits.university is a SPA
that loads data via API calls, so before writing real crawlers we need to
know the actual endpoint paths and JSON shapes (see README.md - "How to
help me discover the API"). Once that's known, replace the bodies below.
"""
from __future__ import annotations

import httpx

from . import save


def fetch_tasks(client: httpx.Client) -> list[dict]:
    """Fetch the full list of tasks/assignments.

    TODO: replace "/api/tasks" with the real endpoint once known.
    Handle pagination if the API paginates results.
    """
    resp = client.get("/api/tasks")
    resp.raise_for_status()
    data = resp.json()
    save.save_json("tasks", "all_tasks", data)
    return data


def fetch_task_detail(client: httpx.Client, task_id: str) -> dict:
    """TODO: replace with the real per-task endpoint."""
    resp = client.get(f"/api/tasks/{task_id}")
    resp.raise_for_status()
    data = resp.json()
    save.save_json("tasks", f"task_{task_id}", data)
    return data


def fetch_my_submissions(client: httpx.Client) -> list[dict]:
    """TODO: replace with the real "my attempts/submissions" endpoint."""
    resp = client.get("/api/submissions/my")
    resp.raise_for_status()
    data = resp.json()
    save.save_json("submissions", "my_submissions", data)
    return data


def fetch_leaderboard(client: httpx.Client) -> dict:
    """TODO: replace with the real leaderboard endpoint."""
    resp = client.get("/api/leaderboard")
    resp.raise_for_status()
    data = resp.json()
    save.save_json("leaderboard", "leaderboard", data)
    return data

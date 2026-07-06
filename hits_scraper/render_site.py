"""Renders the archived output/ data into a self-contained offline HTML
site, loosely styled after code.hits.university's own dark UI (sidebar,
green gradient banner, pill badges, tables) so the archive is pleasant to
browse without the original site.

This does not call the network - it only reads what fetch_everything()
already saved under output/. Run after `cli.py archive`:

    python -m hits_scraper.render_site

Output goes to output/site/index.html (and one page per class/task/
submission alongside it).
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

OUTPUT_ROOT = Path("output")
SITE_ROOT = OUTPUT_ROOT / "site"

VERDICT_STYLES = {
    "ACCEPTED": ("ok", "Accepted"),
    "OK": ("ok", "OK"),
    "PARTIAL SOLUTION": ("warn", "Partial solution"),
    "PENDING": ("pending", "Pending"),
    "NOT SOLVED": ("bad", "Not solved"),
    "NOT OK": ("bad", "Not OK"),
    "WRONG ANSWER": ("bad", "Wrong answer"),
}


def verdict_badge(value: str | None) -> str:
    if not value:
        return '<span class="badge pending">-</span>'
    css, label = VERDICT_STYLES.get(value, ("warn", value))
    return f'<span class="badge {css}">{html.escape(label)}</span>'


def strip_tags(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


PAGE_SHELL = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="logo"><span class="brace">{{</span> CodeHedgehog <span class="brace">}}</span></div>
    <nav class="nav">
      <a class="nav-item" href="index.html">&#127891; Классы</a>
      <a class="nav-item disabled" href="#" title="не архивировалось">&#128172; Поддержка</a>
    </nav>
    <div class="sidebar-bottom">
      <div class="nav-item disabled">&#9789; Тёмная тема</div>
      <div class="nav-item disabled">&#30028; Русский</div>
      <div class="user">
        <div class="avatar"></div>
        <div>
          <div class="user-name">{user_name}</div>
          <div class="user-links"><span class="disabled">Настройки</span> &middot; <span class="disabled">Выйти</span></div>
        </div>
      </div>
    </div>
  </aside>
  <main class="main">
    {banner}
    {tabs}
    <div class="content">
      {content}
    </div>
  </main>
</div>
</body>
</html>
"""

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, "Segoe UI", Arial, sans-serif;
  background: #0f1523;
  color: #e6ebf5;
}
a { color: #4f8ff7; text-decoration: none; }
a:hover { text-decoration: underline; }
.layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #0b1120;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #1b2334;
}
.logo {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(90deg, #6fb8ff, #a5d8ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 28px;
}
.logo .brace { color: #6fb8ff; -webkit-text-fill-color: #6fb8ff; }
.nav { display: flex; flex-direction: column; gap: 4px; }
.nav-item {
  display: block;
  padding: 10px 12px;
  border-radius: 8px;
  color: #cdd6e6;
  font-size: 14px;
}
.nav-item:hover { background: #161d2e; text-decoration: none; }
.nav-item.disabled { color: #5b6478; cursor: default; }
.nav-item.disabled:hover { background: none; }
.sidebar-bottom { margin-top: auto; display: flex; flex-direction: column; gap: 10px; }
.user { display: flex; align-items: center; gap: 10px; margin-top: 8px; padding-top: 14px; border-top: 1px solid #1b2334; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: #3b6fd4; flex-shrink: 0; }
.user-name { font-size: 13px; font-weight: 600; }
.user-links { font-size: 12px; color: #7c8aa8; }
.user-links .disabled { color: #7c8aa8; cursor: default; }
.main { flex: 1; min-width: 0; }
.banner {
  background: linear-gradient(120deg, #0b3b34 0%, #157a5f 60%, #1f9d76 100%);
  padding: 32px 40px;
  position: relative;
  overflow: hidden;
}
.banner h1 { margin: 0 0 6px; font-size: 30px; }
.banner .subtitle { color: #cdeee2; font-size: 15px; }
.banner .deco {
  position: absolute;
  right: -20px; top: -10px; bottom: -10px;
  width: 220px;
  background: repeating-linear-gradient(
    180deg, rgba(255,255,255,0.10) 0 8px, transparent 8px 20px
  );
  opacity: 0.5;
  mask-image: linear-gradient(90deg, transparent, black 40%);
}
.tabs {
  display: flex;
  gap: 4px;
  padding: 0 40px;
  background: #111827;
  border-bottom: 1px solid #1b2334;
}
.tab {
  padding: 14px 16px;
  font-size: 14px;
  color: #9aa5bd;
  border-bottom: 2px solid transparent;
}
.tab.active { color: #eaf1ff; border-color: #4f8ff7; }
.tab.disabled { color: #4a5268; cursor: default; }
.content { padding: 28px 40px 60px; max-width: 1200px; }
h2 { font-size: 26px; margin: 0 0 20px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 24px; align-items: center; }
.search {
  flex: 1;
  background: #1a2233;
  border: 1px solid #2a3450;
  color: #cdd6e6;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
}
.btn {
  background: #24304a;
  border: 1px solid #35426399;
  color: #dfe6f5;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn.primary { background: #2b57c4; border-color: #2b57c4; }
.section-block { margin-bottom: 18px; border: 1px solid #1b2334; border-radius: 10px; overflow: hidden; }
.section-head {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 18px;
  background: #141b2d;
  font-weight: 600;
  cursor: pointer;
}
.section-head .name { flex: 1; }
.pill { padding: 4px 10px; border-radius: 999px; font-size: 12.5px; font-weight: 600; }
.pill.full { background: #123626; color: #4ade80; }
.pill.partial { background: #2a2412; color: #e3b341; }
.pill.empty { background: #241717; color: #f27272; }
table { width: 100%; border-collapse: collapse; }
th {
  text-align: left; font-size: 12.5px; color: #8b96b3;
  padding: 10px 18px; border-top: 1px solid #1b2334;
  text-transform: none;
}
td { padding: 12px 18px; border-top: 1px solid #1b2334; font-size: 14px; vertical-align: top; }
tr:hover td { background: #131b2c; }
.task-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 6px;
  background: #123626; color: #4ade80; font-size: 12.5px; font-weight: 700;
}
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-right: 4px; }
.badge.ok { background: #123626; color: #4ade80; }
.badge.bad { background: #3a1620; color: #f27272; }
.badge.warn { background: #2a2412; color: #e3b341; }
.badge.pending { background: #1c2333; color: #8b96b3; }
.muted { color: #7c8aa8; font-size: 13px; }
.crumb { margin-bottom: 18px; font-size: 13px; }
.badges-row { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.infobox { background: #141b2d; border: 1px solid #1b2334; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; }
.infobox h3 { margin: 22px 0 10px; font-size: 17px; }
.infobox h3:first-child { margin-top: 0; }
.infobox p { line-height: 1.55; color: #dbe2f0; }
.infobox img { max-width: 100%; background: #fff; border-radius: 6px; padding: 6px; margin: 8px 0; }
.examples { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 8px; }
.examples pre, .code-block pre {
  background: #0b1120; border: 1px solid #1b2334; border-radius: 8px;
  padding: 14px; overflow-x: auto; font-size: 13px; white-space: pre-wrap; word-break: break-word;
}
.class-card {
  display: block; padding: 20px 24px; margin-bottom: 14px;
  background: #141b2d; border: 1px solid #1b2334; border-radius: 10px;
}
.class-card .name { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
.class-card .desc { color: #9aa5bd; font-size: 13.5px; }
"""


def page(title: str, banner_title: str, banner_subtitle: str, active_tab: str, content: str, user_name: str) -> str:
    banner = f"""
    <div class="banner">
      <h1>{html.escape(banner_title)}</h1>
      <div class="subtitle">{html.escape(banner_subtitle)}</div>
      <div class="deco"></div>
    </div>
    """
    tab_defs = [
        ("Посты", None),
        ("Задачи", "tasks" if active_tab == "tasks" else None),
        ("Очередь", None),
        ("Ожидающие проверку", None),
        ("Пользователи", None),
        ("Рейтинг", None),
    ]
    tabs_html = []
    for label, marker in tab_defs:
        if marker == active_tab:
            tabs_html.append(f'<div class="tab active">{label}</div>')
        else:
            tabs_html.append(f'<div class="tab disabled" title="не архивировалось">{label}</div>')
    tabs = f'<div class="tabs">{"".join(tabs_html)}</div>'

    return PAGE_SHELL.format(
        title=html.escape(title),
        css=CSS,
        banner=banner,
        tabs=tabs,
        content=content,
        user_name=html.escape(user_name),
    )


def render_index(classes: list[dict], user_name: str) -> str:
    cards = []
    for cls in classes:
        cards.append(
            f'<a class="class-card" href="class_{cls["id"]}.html">'
            f'<div class="name">{html.escape(cls.get("name",""))}</div>'
            f'<div class="desc">{html.escape(cls.get("description") or "")}</div>'
            f"</a>"
        )
    content = f"""
    <h2>Классы</h2>
    {''.join(cards) or '<p class="muted">Архив пуст.</p>'}
    """
    return page("Классы - архив CodeHedgehog", "Мой архив", "code.hits.university (offline)", "", content, user_name)


def score_pill(solved: int, total: int) -> str:
    if total == 0:
        css = "empty"
    elif solved >= total:
        css = "full"
    else:
        css = "partial"
    return f'<span class="pill {css}">{solved}/{total}</span>'


def render_class(cls: dict, tasks_by_section: dict, attempts_by_task: dict, user_name: str) -> str:
    sections = sorted(
        tasks_by_section.values(),
        key=lambda s: min((t["order"] or 0) for t in s["tasks"]),
    )
    blocks = []
    for sec in sections:
        tasks = sorted(sec["tasks"], key=lambda t: t["order"] or 0)
        solved = sum(1 for t in tasks if t["final_verdict"] == "ACCEPTED")
        points_solved = sum(t["max_score"] or 0 for t in tasks if t["final_verdict"] == "ACCEPTED")
        points_total = sum(t["max_score"] or 0 for t in tasks)
        rows = []
        for t in tasks:
            attempts = attempts_by_task.get(t["id"], [])
            last_comment = strip_tags(t.get("last_comment"))
            if len(last_comment) > 80:
                last_comment = last_comment[:80] + "..."
            rows.append(
                f"""
                <tr>
                  <td><span class="task-num">{t['order'] or '-'}</span></td>
                  <td><a href="task_{t['id']}.html">{html.escape(t['name'])}</a></td>
                  <td>{t['max_score'] if t['max_score'] is not None else '-'}</td>
                  <td>{len(attempts)}</td>
                  <td>{verdict_badge(t['final_testing_verdict'])} {verdict_badge(t['final_verdict'])}</td>
                  <td class="muted">{html.escape(last_comment) if last_comment else '-'}</td>
                </tr>
                """
            )
        blocks.append(
            f"""
            <div class="section-block">
              <div class="section-head">
                <span class="name">{html.escape(sec['name'])}</span>
                {score_pill(solved, len(tasks))} задач
                {score_pill(points_solved, points_total)} баллов
              </div>
              <table>
                <tr><th>#</th><th>Имя</th><th>Баллы</th><th>Попыток</th><th>Вердикт(ы)</th><th>Последний комментарий</th></tr>
                {''.join(rows)}
              </table>
            </div>
            """
        )

    content = f"""
    <div class="toolbar">
      <input class="search" placeholder="Начните вводить название задачи" oninput="filterTasks(this.value)">
      <a class="btn" href="index.html">&larr; Назад</a>
    </div>
    <h2>Задачи</h2>
    <div id="sections">{''.join(blocks)}</div>
    <script>
    function filterTasks(q) {{
      q = q.toLowerCase();
      document.querySelectorAll('#sections tr').forEach(function(row) {{
        if (row.querySelector('th')) return;
        var name = row.children[1] ? row.children[1].textContent.toLowerCase() : '';
        row.style.display = name.indexOf(q) === -1 ? 'none' : '';
      }});
    }}
    </script>
    """
    return page(
        f"{cls.get('name')} - Задачи",
        cls.get("name", ""),
        cls.get("description") or "Высшая IT Школа",
        "tasks",
        content,
        user_name,
    )


def render_task(task: dict, class_name: str, class_id: str, attempts: list[dict], user_name: str) -> str:
    examples_html = ""
    if task.get("examples"):
        cards = []
        for ex in task["examples"]:
            cards.append(
                f"""
                <div>
                  <div class="muted">Входные данные</div>
                  <pre>{html.escape(ex.get('example_input_data') or '')}</pre>
                </div>
                <div>
                  <div class="muted">Выходные данные</div>
                  <pre>{html.escape(ex.get('example_output_data') or '')}</pre>
                </div>
                """
            )
        examples_html = f'<h3>Примеры</h3><div class="examples">{"".join(cards)}</div>'

    attempts_sorted = sorted(attempts, key=lambda a: a.get("created_at") or "", reverse=True)
    attempt_rows = []
    for a in attempts_sorted:
        attempt_rows.append(
            f"""
            <tr>
              <td>{html.escape(a.get('created_at',''))}</td>
              <td>{html.escape(a.get('programming_language_name') or '')}</td>
              <td>{verdict_badge(a.get('testing_verdict'))}</td>
              <td>{verdict_badge(a.get('postmoderation_verdict'))}</td>
              <td>{a.get('actual_score', '-')}</td>
              <td><a href="submission_{a['id']}.html">открыть</a></td>
            </tr>
            """
        )

    content = f"""
    <div class="crumb"><a href="class_{class_id}.html">&larr; {html.escape(class_name)}</a></div>
    <h2>{html.escape(task['name'])}</h2>
    <div class="badges-row">
      <span class="badge pending">Баллы за задачу &mdash; {task.get('max_score','-')}</span>
      <span class="badge pending">Успешные решения &mdash; {task.get('solved_count','-')}</span>
      {verdict_badge(task.get('final_testing_verdict'))}
      {verdict_badge(task.get('final_verdict'))}
    </div>
    <div class="infobox">
      <h3>Условие</h3>
      {task.get('description') or ''}
      <h3>Входные данные</h3>
      {task.get('input_data_description') or ''}
      <h3>Выходные данные</h3>
      {task.get('output_data_description') or ''}
      <h3>Ограничения</h3>
      <p>Время &mdash; {task.get('time_limit')} ms, память &mdash; {task.get('memory_limit')} bytes</p>
      {examples_html}
    </div>
    <h2>Мои посылки</h2>
    <table>
      <tr><th>Время отправки</th><th>Язык</th><th>Вердикт тестирования</th><th>Вердикт постмодерации</th><th>Баллы</th><th></th></tr>
      {''.join(attempt_rows) or '<tr><td class="muted" colspan="6">Посылок нет</td></tr>'}
    </table>
    """
    return page(f"{task['name']} - задача", class_name, "Высшая IT Школа", "tasks", content, user_name)


def render_submission(submission: dict, task_name: str, task_id: str, comments: list[dict], user_name: str) -> str:
    contents = submission.get("contents") or []
    code_blocks = []
    for i, c in enumerate(contents):
        label = f"Файл {i + 1}" if len(contents) > 1 else "Код"
        code_blocks.append(f'<div class="muted">{label}</div><div class="code-block"><pre>{html.escape(c)}</pre></div>')

    test_rows = []
    for run in submission.get("checker_runs") or []:
        for t in run.get("checker_run_on_tests") or []:
            test_rows.append(
                f"""
                <tr>
                  <td>{verdict_badge(t.get('testing_verdict'))}</td>
                  <td>{html.escape(t.get('comment') or '')}</td>
                  <td>{t.get('time','-')} ms</td>
                  <td>{t.get('memory','-')} bytes</td>
                </tr>
                """
            )

    comment_blocks = []
    for c in comments:
        comment_blocks.append(
            f"""
            <div class="infobox">
              <div class="muted">{html.escape(c.get('author_name') or c.get('sender_name') or '')} &middot; {html.escape(c.get('created_at') or '')}</div>
              <div>{c.get('text') or c.get('content') or ''}</div>
            </div>
            """
        )

    content = f"""
    <div class="crumb"><a href="task_{task_id}.html">&larr; {html.escape(task_name)}</a></div>
    <h2>Посылка &middot; {html.escape(submission.get('programming_language_name') or '')}</h2>
    <div class="badges-row">
      {verdict_badge(submission.get('testing_verdict'))}
      {verdict_badge(submission.get('postmoderation_verdict'))}
      {verdict_badge(submission.get('final_testing_verdict'))}
      <span class="badge pending">Баллы: {submission.get('actual_score','-')}/{submission.get('testing_score','-')}</span>
    </div>
    {''.join(code_blocks)}
    <h3 style="margin-top:24px;">Результаты тестов</h3>
    <table>
      <tr><th>Вердикт</th><th>Комментарий</th><th>Время</th><th>Память</th></tr>
      {''.join(test_rows) or '<tr><td class="muted" colspan="4">Нет данных о тестах</td></tr>'}
    </table>
    {"<h3 style='margin-top:24px;'>Комментарии</h3>" + "".join(comment_blocks) if comment_blocks else ""}
    """
    return page("Посылка", task_name, "Высшая IT Школа", "tasks", content, user_name)


def main() -> None:
    SITE_ROOT.mkdir(parents=True, exist_ok=True)

    me = load_json(OUTPUT_ROOT / "user" / "me.json")
    user_name = (me or {}).get("user", {}).get("name", "")

    classes = load_json(OUTPUT_ROOT / "classes" / "all_classes.json") or []
    (SITE_ROOT / "index.html").write_text(render_index(classes, user_name), encoding="utf-8")

    for cls in classes:
        class_id = cls["id"]
        attempts = load_json(OUTPUT_ROOT / "classes" / class_id / "my_attempts.json") or []
        attempts_by_task: dict[str, list[dict]] = {}
        for a in attempts:
            attempts_by_task.setdefault(a["task_id"], []).append(a)

        tasks_by_section: dict[str, dict] = {}
        for task_id in attempts_by_task:
            task_file = load_json(OUTPUT_ROOT / "tasks" / f"task_{task_id}.json")
            if not task_file:
                continue
            t = task_file["class_task"]
            section = t.get("class_section") or {"id": "unknown", "name": "Без раздела"}
            bucket = tasks_by_section.setdefault(section["id"], {"name": section.get("name", "Без раздела"), "tasks": []})
            bucket["tasks"].append(t)

            attempts_for_task = attempts_by_task[task_id]
            (SITE_ROOT / f"task_{task_id}.html").write_text(
                render_task(t, cls.get("name", ""), class_id, attempts_for_task, user_name),
                encoding="utf-8",
            )

            for a in attempts_for_task:
                solution_id = a["solution_id"]
                submission_id = a["id"]
                sub_file = load_json(OUTPUT_ROOT / "solutions" / solution_id / f"submission_{submission_id}.json")
                if not sub_file:
                    continue
                comments_file = load_json(OUTPUT_ROOT / "solutions" / solution_id / "comments.json")
                comments = (comments_file or {}).get("comments", [])
                (SITE_ROOT / f"submission_{submission_id}.html").write_text(
                    render_submission(sub_file["submission"], t["name"], task_id, comments, user_name),
                    encoding="utf-8",
                )

        (SITE_ROOT / f"class_{class_id}.html").write_text(
            render_class(cls, tasks_by_section, attempts_by_task, user_name),
            encoding="utf-8",
        )

    print(f"wrote {SITE_ROOT}/index.html and {len(classes)} class page(s)")


if __name__ == "__main__":
    main()

# mypy: disable-error-code="arg-type"
# Values read from live API responses are untyped; this script checks them at run time.
"""Smoke test against a live Atlassian Cloud site.

By default it only reads. Nothing is created, changed or deleted, so it is safe
to run against a production site. Jira's search and count are ``POST`` requests
(``/search/jql`` and ``/search/approximate-count``) but do not change anything.

Usage::

    export ATLASSIAN_URL=https://your-site.atlassian.net
    export ATLASSIAN_EMAIL=you@example.com
    export ATLASSIAN_API_TOKEN=...        # https://id.atlassian.com/manage-profile/security/api-tokens
    export JIRA_PROJECT=ABC               # optional, defaults to the first project
    export CONFLUENCE_SPACE=DOC           # optional, defaults to the first space
    python scripts/cloud_smoke_test.py

It prints one line per check and exits with 1 if any check failed. A check is
skipped when the site has nothing to test it with (for example, no issues).

Optional settings:

``JIRA_ISSUE`` / ``CONFLUENCE_PAGE_ID``
    The issue and page to read, instead of the most recent issue and the
    first page. Point them at ones that have an attachment.
``SMOKE_STRICT=1``
    Treat a skipped check as a failure. The nightly CI run uses this, so an
    empty site cannot pass.

``--seed`` is the only mode that writes. On a test site, it creates what the
read-only checks need (three issues and three pages named "Smoke test
fixture", with an attachment, a label and a comment) in ``JIRA_PROJECT`` and
``CONFLUENCE_SPACE``, which must both be set, and prints the values for
``JIRA_ISSUE`` and ``CONFLUENCE_PAGE_ID``. Running it again reuses the
fixtures it finds::

    python scripts/cloud_smoke_test.py --seed
"""

from __future__ import annotations

import os
import sys
import traceback
from collections.abc import Callable
from itertools import islice
from typing import Any

from atlassian_api import Confluence, Jira

FIXTURE_NAME = "Smoke test fixture"
FIXTURE_LABEL = "smoke-test-fixture"
FIXTURE_FILE = ("smoke-test.txt", b"atlassian-api-py smoke test fixture\n")
FIXTURE_NOTE = "Created by scripts/cloud_smoke_test.py --seed"

results: list[tuple[str, str, str]] = []


def env(name: str) -> str | None:
    """Return an environment variable, or ``None`` when unset or blank.

    CI passes unset secrets and variables as empty strings.
    """
    return (os.environ.get(name) or "").strip() or None


def skip(name: str, why: str) -> None:
    """Record checks that could not run."""
    results.append(("SKIP", name, why))
    print(f"SKIP  {name}: {why}")


def value(obj: Any, name: str) -> Any:
    """Read ``name`` from a dict or a ``SimpleNamespace``."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def check(name: str, func: Callable[[], Any]) -> Any:
    """Run one check, record PASS/FAIL/SKIP and return its result."""
    try:
        outcome = func()
    except Skip as skipped:
        skip(name, str(skipped))
        return None
    except Exception as error:  # noqa: BLE001 - report every failure
        detail = f"{type(error).__name__}: {str(error)[:200]}"
        results.append(("FAIL", name, detail))
        print(f"FAIL  {name}: {detail}")
        if env("SMOKE_TRACEBACK"):
            traceback.print_exc()
        return None
    detail, returned = outcome if isinstance(outcome, tuple) else (outcome, outcome)
    results.append(("PASS", name, str(detail)))
    print(f"PASS  {name}: {detail}")
    return returned


class Skip(Exception):
    """Nothing on the site to run this check with."""


def need(obj: Any, why: str) -> Any:
    if not obj:
        raise Skip(why)
    return obj


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def jira_checks(url: str, email: str, token: str) -> None:
    jira = Jira(url=url, username=email, password=token)

    me = check("jira: /myself (authentication)", lambda: _myself(jira))
    if me is None:
        return  # nothing else can work without authentication
    check("jira.user(accountId)", lambda: _user(jira, me))
    check("jira.search_users()", lambda: _search_users(jira, me))

    projects = check("jira.get_projects()", lambda: _projects(jira))
    key = env("JIRA_PROJECT") or (value(projects[0], "key") if projects else None)
    project = check("jira.get_project()", lambda: _project(jira, key))
    if project is not None:
        check("jira.get_versions()", lambda: _count(jira.get_versions(key)))
        check(
            "jira.get_project_components()",
            lambda: _count(jira.get_project_components(value(project, "id"))),
        )

    jql = f'project = "{key}" ORDER BY updated DESC' if key else "ORDER BY updated DESC"
    issues = check("jira.search_issue_with_jql()", lambda: _search(jira, jql))
    check("jira.iter_issues() pages past 1", lambda: _iter(jira, jql))
    check("jira.count_issues()", lambda: f"{jira.count_issues(jql)} issues")
    check("jira.get_fields() / get_field_id()", lambda: _fields(jira))

    issue_key = env("JIRA_ISSUE") or (value(issues[0], "key") if issues else None)
    issue = check("jira.issue()", lambda: _issue(jira, issue_key))
    if issue is None:
        return
    check("jira.issue_changelog()", lambda: _changelog(jira, issue_key))
    check(
        "jira.get_issue_comments()", lambda: _count(jira.get_issue_comments(issue_key))
    )
    check(
        "jira.get_issue_watchers()", lambda: _count(jira.get_issue_watchers(issue_key))
    )
    check("jira.get_transitions()", lambda: _count(jira.get_transitions(issue_key)))
    check("jira.get_worklogs()", lambda: _count(jira.get_worklogs(issue_key)))
    check("jira.download_attachment()", lambda: _jira_attachment(jira, issue))


def _myself(jira: Jira) -> tuple[str, Any]:
    me = jira.get("/rest/api/2/myself")
    account = value(me, "accountId")
    expect(bool(account), f"no accountId in /myself: {me!r}"[:200])
    return f"signed in as {value(me, 'displayName')}", me


def _user(jira: Jira, me: Any) -> str:
    user = jira.user(value(me, "accountId"))
    expect(value(user, "accountId") == value(me, "accountId"), "wrong user returned")
    return "found by accountId"


def _search_users(jira: Jira, me: Any) -> str:
    users = jira.search_users(str(value(me, "displayName") or "a"), max_results=5)
    expect(isinstance(users, list), f"expected a list, got {type(users).__name__}")
    return f"{len(users)} users"


def _projects(jira: Jira) -> tuple[str, Any]:
    projects = jira.get_projects()
    expect(
        isinstance(projects, list), f"expected a list, got {type(projects).__name__}"
    )
    return f"{len(projects)} projects", projects


def _project(jira: Jira, key: str | None) -> tuple[str, Any]:
    need(key, "no project on the site; set JIRA_PROJECT")
    project = jira.get_project(key)
    expect(value(project, "key") == key, f"wrong project: {project!r}"[:200])
    return f"{key} (id {value(project, 'id')})", project


def _search(jira: Jira, jql: str) -> tuple[str, Any]:
    issues = jira.search_issue_with_jql(jql, max_result=5)
    expect(isinstance(issues, list), "expected a list")
    expect(
        not issues or value(value(issues[0], "fields"), "summary") is not None,
        "issues came back without fields (only IDs)",
    )
    return f"{len(issues)} issues with fields", issues


def _iter(jira: Jira, jql: str) -> str:
    # page_size=2 forces several nextPageToken requests on a small project.
    keys = [value(i, "key") for i in islice(jira.iter_issues(jql, page_size=2), 5)]
    expect(len(keys) == len(set(keys)), f"duplicate issues across pages: {keys}")
    return f"{len(keys)} distinct issues over pages of 2"


def _fields(jira: Jira) -> str:
    fields = jira.get_fields()
    expect(isinstance(fields, list) and len(fields) > 0, "no fields")
    return f"{len(fields)} fields, Summary = {jira.get_field_id('Summary')}"


def _issue(jira: Jira, key: str | None) -> tuple[str, Any]:
    need(key, "no issues in the project")
    issue = jira.issue(key)
    expect(value(issue, "key") == key, "wrong issue returned")
    return str(key), issue


def _changelog(jira: Jira, key: str) -> str:
    issue = jira.issue_changelog(key)
    histories = value(value(issue, "changelog"), "histories")
    expect(isinstance(histories, list), "no changelog.histories list")
    return f"{len(histories)} history entries"


def _jira_attachment(jira: Jira, issue: Any) -> str:
    attachments = value(value(issue, "fields"), "attachment") or []
    first = need(attachments, "the issue has no attachments")[0]
    data = jira.download_attachment(str(value(first, "id")))
    expect(isinstance(data, bytes), "expected bytes")
    return f"{value(first, 'filename')}: {len(data)} bytes"


def confluence_checks(url: str, email: str, token: str) -> None:
    confluence = Confluence(url=url, username=email, password=token)

    spaces = check("confluence.get_spaces()", lambda: _spaces(confluence))
    if spaces is None:
        return
    key = env("CONFLUENCE_SPACE") or (value(spaces[0], "key") if spaces else None)
    check("confluence.get_space()", lambda: _space(confluence, key))
    pages = check("confluence.get_content_by_space()", lambda: _pages(confluence, key))
    check(
        "confluence.get_content_by_space(blogpost)",
        lambda: _size(confluence.get_content_by_space(key, "blogpost", limit=3)),
    )
    check(
        "confluence.search_content() cursor paging", lambda: _search_c(confluence, key)
    )
    check("confluence.iter_search()", lambda: _iter_c(confluence, key))

    pinned = env("CONFLUENCE_PAGE_ID")
    if pinned:
        page = check(
            "confluence: CONFLUENCE_PAGE_ID",
            lambda: _pinned_page(confluence, pinned),
        )
    else:
        page = pages[0] if pages else None
        if page is None:
            skip("confluence page checks", "the space has no pages")
    if page is None:
        return
    page_id = value(page, "id")
    check("confluence.get_page_by_title()", lambda: _by_title(confluence, key, page))
    check("confluence.get_content_by_id()", lambda: _by_id(confluence, page_id))
    check(
        "confluence.get_content_history()",
        lambda: _count(confluence.get_content_history(page_id)),
    )
    check(
        "confluence.get_child_pages()",
        lambda: _size(confluence.get_child_pages(page_id)),
    )
    check("confluence.get_labels()", lambda: _size(confluence.get_labels(page_id)))
    check("confluence.get_comments()", lambda: _size(confluence.get_comments(page_id)))
    attachments = check(
        "confluence.get_attachments()",
        lambda: _with_results(confluence.get_attachments(page_id)),
    )
    check(
        "confluence.download_attachment()",
        lambda: _conf_attachment(confluence, page_id, attachments),
    )


def _spaces(confluence: Confluence) -> tuple[str, Any]:
    spaces = confluence.get_spaces(limit=5)
    expect(value(spaces, "size") is not None, "missing v1 envelope (size)")
    return f"{value(spaces, 'size')} spaces", value(spaces, "results")


def _space(confluence: Confluence, key: str | None) -> str:
    need(key, "no space on the site; set CONFLUENCE_SPACE")
    space = confluence.get_space(key)
    return f"{key} (id {value(space, 'id')})"


def _pages(confluence: Confluence, key: str | None) -> tuple[str, Any]:
    need(key, "no space on the site")
    result = confluence.get_content_by_space(key, start=0, limit=3)
    results = value(result, "results") or []
    archived = [p for p in results if value(p, "status") not in (None, "current")]
    expect(not archived, f"archived pages listed: {[value(p, 'id') for p in archived]}")
    return f"{len(results)} current pages", results


def _pinned_page(confluence: Confluence, page_id: str) -> tuple[str, Any]:
    page = confluence.get_content_by_id(page_id)
    expect(str(value(page, "id")) == page_id, f"page {page_id} not returned")
    return f"page {page_id}", page


def _search_c(confluence: Confluence, key: str | None) -> str:
    cql = f'space = "{key}" and type = page' if key else "type = page"
    first = value(confluence.search_content(cql, start=0, limit=2), "results") or []
    second = value(confluence.search_content(cql, start=2, limit=2), "results") or []
    ids = [value(r, "id") for r in first + second]
    expect(len(ids) == len(set(ids)), f"start= returned the same results again: {ids}")
    return f"{len(first)} + {len(second)} distinct results"


def _iter_c(confluence: Confluence, key: str | None) -> str:
    cql = f'space = "{key}" and type = page' if key else "type = page"
    ids = [value(r, "id") for r in islice(confluence.iter_search(cql, page_size=2), 5)]
    expect(len(ids) == len(set(ids)), f"duplicates across pages: {ids}")
    return f"{len(ids)} distinct results over pages of 2"


def _by_title(confluence: Confluence, key: str | None, page: Any) -> str:
    result = confluence.get_page_by_title(key, value(page, "title"))
    expect(value(result, "size") is not None, "missing v1 envelope (size)")
    ids = [value(p, "id") for p in value(result, "results") or []]
    expect(value(page, "id") in ids, f"page {value(page, 'id')} not found by title")
    return f"found {value(page, 'title')!r}"


def _by_id(confluence: Confluence, page_id: Any) -> str:
    page = confluence.get_content_by_id(page_id)
    storage = value(value(value(page, "body"), "storage"), "value")
    expect(storage is not None, "no body.storage.value")
    return f"{len(storage)} characters of storage format"


def _conf_attachment(confluence: Confluence, page_id: Any, attachments: Any) -> str:
    first = need(attachments, "the page has no attachments")[0]
    data = confluence.download_attachment(page_id, value(first, "title"))
    expect(isinstance(data, bytes), "expected bytes")
    return f"{value(first, 'title')}: {len(data)} bytes"


def _count(result: Any) -> str:
    """Describe a list, or a response holding a list, without asserting more."""
    if isinstance(result, list):
        return f"{len(result)} items"
    for name in (
        "results",
        "values",
        "comments",
        "worklogs",
        "transitions",
        "watchers",
    ):
        items = value(result, name)
        if isinstance(items, list):
            return f"{len(items)} {name}"
    expect(result is not None, "empty response")
    return "ok"


def _size(result: Any) -> str:
    expect(value(result, "size") is not None, "missing v1 envelope (size)")
    return f"{value(result, 'size')} items"


def _with_results(result: Any) -> tuple[str, Any]:
    return _size(result), value(result, "results")


def seed(url: str, email: str, token: str) -> int:
    """Create the fixtures the read-only checks need. The only mode that writes."""
    project, space = env("JIRA_PROJECT"), env("CONFLUENCE_SPACE")
    if not (project and space):
        print(
            "--seed needs JIRA_PROJECT and CONFLUENCE_SPACE: it only writes "
            "where you tell it to."
        )
        return 2
    print(
        f"Creating fixtures in Jira project {project} and Confluence space "
        f"{space} on {url}\n"
    )
    jira = Jira(url=url, username=email, password=token)
    confluence = Confluence(url=url, username=email, password=token)
    issue_key = check("seed: Jira issues", lambda: _seed_issues(jira, project))
    page_id = check("seed: Confluence pages", lambda: _seed_pages(confluence, space))
    if issue_key is None or page_id is None:
        return 1
    print("\nSet these for the read-only run (as repository variables for CI):\n")
    for name, setting in (
        ("JIRA_PROJECT", project),
        ("JIRA_ISSUE", issue_key),
        ("CONFLUENCE_SPACE", space),
        ("CONFLUENCE_PAGE_ID", page_id),
    ):
        print(f"gh variable set {name} --body {setting}")
    return 0


def _seed_issues(jira: Jira, project: str) -> tuple[str, str]:
    jql = f'project = "{project}" AND labels = "{FIXTURE_LABEL}" ORDER BY created ASC'
    keys = [value(i, "key") for i in jira.search_issue_with_jql(jql, max_result=10)]
    for number in range(len(keys) + 1, 4):
        created = jira.create_issue(
            {
                "project": {"key": project},
                "summary": f"{FIXTURE_NAME} {number}",
                "issuetype": {"name": env("JIRA_ISSUE_TYPE") or "Task"},
                "labels": [FIXTURE_LABEL],
            }
        )
        keys.append(value(created, "key"))
    first = keys[0]
    if not (value(value(jira.issue(first), "fields"), "attachment") or []):
        jira.add_attachment(first, *FIXTURE_FILE, "text/plain")
        jira.add_issue_comment(first, FIXTURE_NOTE)
    return f"{', '.join(keys)}; attachment and comment on {first}", first


def _seed_pages(confluence: Confluence, space: str) -> tuple[str, str]:
    ids = []
    for number in (1, 2, 3):
        title = f"{FIXTURE_NAME} {number}"
        found = value(confluence.get_page_by_title(space, title), "results") or []
        page = (
            found[0]
            if found
            else confluence.create_content(title, space, f"<p>{FIXTURE_NOTE}</p>")
        )
        ids.append(str(value(page, "id")))
    first = ids[0]
    if not (value(confluence.get_attachments(first), "results") or []):
        confluence.upload_attachment(first, *FIXTURE_FILE, "text/plain")
    if not (value(confluence.get_labels(first), "results") or []):
        confluence.add_label(first, FIXTURE_LABEL)
    if not (value(confluence.get_comments(first), "results") or []):
        confluence.add_comment(first, f"<p>{FIXTURE_NOTE}</p>")
    return f"pages {', '.join(ids)}; attachment, label and comment on {first}", first


def write_step_summary(headline: str) -> None:
    """Add a results table to the GitHub Actions run page, when run there."""
    path = env("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [f"### Cloud smoke test: {headline}", "", "| Result | Check | Detail |"]
    lines.append("|---|---|---|")
    for status, name, detail in results:
        cell = detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {status} | `{name}` | {cell} |")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    settings = {
        name: env(name)
        for name in ("ATLASSIAN_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN")
    }
    missing = [name for name, setting in settings.items() if not setting]
    if missing:
        print(f"Set {', '.join(missing)} (see the docstring at the top of this file).")
        return 2
    url, email, token = (str(setting) for setting in settings.values())
    if not Jira(url=url).cloud:
        print("The URL is not an Atlassian Cloud site (*.atlassian.net).")
        return 2
    if args == ["--seed"]:
        return seed(url, email, token)
    if args:
        print(f"Unknown arguments: {' '.join(args)}. The only option is --seed.")
        return 2
    print(f"Read-only smoke test against {url}\n")
    jira_checks(url, email, token)
    print()
    confluence_checks(url, email, token)
    counts = {s: sum(1 for r in results if r[0] == s) for s in ("PASS", "FAIL", "SKIP")}
    headline = (
        f"{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped"
    )
    print(f"\n{headline}")
    write_step_summary(headline)
    if counts["FAIL"]:
        return 1
    if counts["SKIP"] and env("SMOKE_STRICT"):
        print(
            "SMOKE_STRICT is set, so skipped checks fail the run. Give the site "
            "data to read: see --seed in the docstring at the top of this file."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

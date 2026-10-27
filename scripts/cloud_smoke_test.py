# mypy: disable-error-code="arg-type"
# Values read from live API responses are untyped; this script checks them at run time.
"""Read-only smoke test against a live Atlassian Cloud site.

It only reads. Nothing is created, changed or deleted, so it is safe to run
against a production site. Jira's search and count are ``POST`` requests
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
"""

from __future__ import annotations

import os
import sys
import traceback
from collections.abc import Callable
from itertools import islice
from typing import Any

from atlassian_api import Confluence, Jira

results: list[tuple[str, str, str]] = []


def value(obj: Any, name: str) -> Any:
    """Read ``name`` from a dict or a ``SimpleNamespace``."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def check(name: str, func: Callable[[], Any]) -> Any:
    """Run one check, record PASS/FAIL/SKIP and return its result."""
    try:
        outcome = func()
    except Skip as skip:
        results.append(("SKIP", name, str(skip)))
        print(f"SKIP  {name}: {skip}")
        return None
    except Exception as error:  # noqa: BLE001 - report every failure
        detail = f"{type(error).__name__}: {str(error)[:200]}"
        results.append(("FAIL", name, detail))
        print(f"FAIL  {name}: {detail}")
        if os.environ.get("SMOKE_TRACEBACK"):
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
    key = os.environ.get("JIRA_PROJECT") or (
        value(projects[0], "key") if projects else None
    )
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

    issue_key = value(issues[0], "key") if issues else None
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
    key = os.environ.get("CONFLUENCE_SPACE") or (
        value(spaces[0], "key") if spaces else None
    )
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

    page = pages[0] if pages else None
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


def main() -> int:
    try:
        url = os.environ["ATLASSIAN_URL"]
        email = os.environ["ATLASSIAN_EMAIL"]
        token = os.environ["ATLASSIAN_API_TOKEN"]
    except KeyError as missing:
        print(f"Set {missing.args[0]} (see the docstring at the top of this file).")
        return 2
    print(f"Read-only smoke test against {url}\n")
    if not Jira(url=url).cloud:
        print("The URL is not an Atlassian Cloud site (*.atlassian.net).")
        return 2
    jira_checks(url, email, token)
    print()
    confluence_checks(url, email, token)
    failed = [r for r in results if r[0] == "FAIL"]
    counts = {s: sum(1 for r in results if r[0] == s) for s in ("PASS", "FAIL", "SKIP")}
    print(
        f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

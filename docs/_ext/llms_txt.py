"""Write ``llms.txt`` and ``llms-full.txt`` next to the HTML documentation.

`llms.txt <https://llmstxt.org/>`_ is a short Markdown index that AI
assistants and coding agents read instead of crawling HTML. ``llms-full.txt``
is the whole reference in one file. Read the Docs serves both from the root of
the documentation domain.

The API reference is generated from the code, so it cannot fall behind it:
every public method of the three clients, with its signature and docstring.
"""

from __future__ import annotations

import inspect
import re
import textwrap
from pathlib import Path
from typing import Any

import atlassian_api
from atlassian_api import _hints, error
from atlassian_api.client import AtlassianAPI

DOCS = "https://atlassian-api-py.readthedocs.io/en/latest"
REPO = "https://github.com/shenxianpeng/atlassian-api-py"
CLIENTS = (atlassian_api.Jira, atlassian_api.Confluence, atlassian_api.Bitbucket)

SUMMARY = (
    "Python client for the Jira, Confluence and Bitbucket REST APIs. The same "
    "Jira and Confluence code runs against Atlassian Data Center and Atlassian "
    "Cloud, it installs next to atlassian-python-api (the import package is "
    "`atlassian_api`), and its only dependency is `requests`."
)

FACTS = """\
Facts to get right when writing code with this library:

- Install with `pip install atlassian-api-py` (version 2.0 or later, Python 3.10 or later).
- Import with `from atlassian_api import Jira, Confluence, Bitbucket`. The import package is `atlassian_api`. The package named `atlassian` belongs to a different library, atlassian-python-api.
- Method names are not those of atlassian-python-api or of the `jira` package. For example a JQL search is `jira.search_issue_with_jql()` or `jira.iter_issues()`, not `jql()` or `search_issues()`. Calling a name from those libraries raises `AttributeError` with the method to use instead.
- Data Center: pass a personal access token as `token=`. Cloud: pass the account email as `username=` and an API token as `password=`.
- Cloud is detected from the URL (`*.atlassian.net`, `*.jira.com`, `api.atlassian.com`). Pass `cloud=True` for a Cloud site on a custom domain. The same method names and arguments work on both; users are usernames on Data Center and `accountId` values on Cloud.
- Read methods return nested `types.SimpleNamespace` objects: `issue.fields.status.name`, not `issue["fields"]["status"]["name"]`. A missing field raises `AttributeError`, so use `getattr(obj, "field", None)` for optional fields.
- `Jira.search_issue_with_jql()` returns a list of dictionaries and `Jira.iter_issues()` yields dictionaries: `issue["key"]`, `issue["fields"]["summary"]`.
- Methods that create, update or delete return the decoded JSON as a dictionary, or `None` when the response has no body.
- HTTP errors raise `atlassian_api.error.APIError` or a subclass (`NotFoundError`, `AuthenticationError`, `PermissionDeniedError`, `ConflictError`, `RateLimitError`, `ServerError`), with `.code` and `.message`. They are not `requests` exceptions.
- HTTP 429 is retried automatically, honouring `Retry-After` (`max_retries=3`, `max_retry_wait=60` seconds by default).
- For Confluence Cloud pass the site URL without `/wiki`; it is added for you.
- The Bitbucket client is for Bitbucket Server and Data Center only. A `bitbucket.org` URL raises `ValueError`.
- For an endpoint without a helper, use `client.get(path, params=...)`, `client.post(path, json=...)`, `client.put(...)`, `client.delete(...)` with the REST path below the base URL.
"""

NOT_COVERED = """\
- Bitbucket Cloud.
- Jira Service Management, filters, dashboards, permissions, and project or user administration.
- Confluence space administration, templates, restrictions and page moves.
- Bamboo, Crowd, Xray, Assets and other Atlassian products.
- OAuth 1.0a and Kerberos set-up (pass your own `requests.Session` as `session=`).
- An async client: the clients are synchronous.

atlassian-python-api covers most of these. Both libraries can be installed in the same environment.
"""

EXAMPLES = '''\
```python
from atlassian_api import Confluence, Jira
from atlassian_api.error import APIError, NotFoundError

# Data Center: personal access token
jira = Jira(url="https://jira.company.com", token="personal-access-token")

# Cloud: account email and API token. Same methods as above.
jira = Jira(
    url="https://your-site.atlassian.net",
    username="you@example.com",
    password="api-token",
)

# Read an issue: attribute access
issue = jira.issue("TEST-1")
print(issue.key, issue.fields.summary, issue.fields.status.name)

# Search: every page is fetched; issues are dictionaries
for found in jira.iter_issues("project = TEST AND status = Open", fields=["summary"]):
    print(found["key"], found["fields"]["summary"])
print(jira.count_issues("project = TEST AND status = Open"))

# Create, comment, transition
created = jira.create_issue(
    {"project": {"key": "TEST"}, "summary": "From a script", "issuetype": {"name": "Task"}}
)
jira.add_issue_comment(created["key"], "Created by automation.")
transitions = jira.get_transitions(created["key"]).transitions
jira.issue_transition(created["key"], transitions[0].id)

# Errors
try:
    jira.issue("MISSING-1")
except NotFoundError:
    print("no such issue")
except APIError as exc:
    print(exc.code, exc.message)

# Sprint report
board = jira.get_boards(project="TEST", board_type="scrum")[0]
sprint = jira.get_board_sprints(board.id, state="active")[0]
for item in jira.iter_sprint_issues(sprint.id, fields=["summary", "status"]):
    print(item.key, item.fields.status.name, item.fields.summary)

# Confluence: create a page, or update it when the title exists
confluence = Confluence(
    url="https://your-site.atlassian.net",
    username="you@example.com",
    password="api-token",
)
confluence.create_or_update_page("DOCS", "Nightly report", "<p>All green</p>")
for page in confluence.get_content_by_space("DOCS", limit=50).results:
    print(page.id, page.title)
```
'''


def public_methods(cls: type) -> list[tuple[str, Any]]:
    """Return the public methods ``cls`` defines itself, in source order."""
    methods = [
        (name, member)
        for name, member in vars(cls).items()
        if inspect.isfunction(member) and not name.startswith("_")
    ]
    return sorted(methods, key=lambda item: item[1].__code__.co_firstlineno)


def _inline(text: str) -> str:
    """Turn the reStructuredText inline markup used in docstrings into Markdown."""
    text = re.sub(r":(?:meth|func):`~?(?:[\w.]+\.)?(\w+)`", r"`\1()`", text)
    text = re.sub(r":(?:class|exc|data|attr|mod):`~?(?:[\w.]+\.)?(\w+)`", r"`\1`", text)
    text = re.sub(r"`([^`<]+?)\s*<([^>]+)>`_+", r"[\1](\2)", text)
    return text.replace("``", "`")


def docstring_markdown(doc: str | None) -> str:
    """Render a Sphinx-style docstring as Markdown.

    Prose and ``code-block`` examples are kept; ``:param:``, ``:return:`` and
    ``:raises:`` fields become a list; ``:type:`` and ``:rtype:`` are dropped
    because the signature already carries the types.
    """
    lines = inspect.cleandoc(doc or "").splitlines()
    body: list[str] = []
    fields: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        field = re.match(r":(\w+)(?: ([^:]+))?:\s*(.*)", line)
        if field:
            kind, name, text = field.groups()
            index += 1
            while index < len(lines) and lines[index].startswith(" "):
                text += " " + lines[index].strip()
                index += 1
            text = _inline(text.strip())
            if kind == "param":
                fields.append(f"- `{name}`: {text}")
            elif kind in ("return", "returns"):
                fields.append(f"- Returns: {text}")
            elif kind in ("raises", "raise"):
                fields.append(f"- Raises `{name}`: {text}")
            continue
        block = re.match(r"\.\. code-block:: (\w+)", line)
        if block:
            index += 1
            code = []
            while index < len(lines) and (
                not lines[index].strip() or lines[index].startswith(" ")
            ):
                code.append(lines[index])
                index += 1
            source = textwrap.dedent("\n".join(code)).strip("\n")
            body += [f"```{block.group(1)}", source, "```", ""]
            continue
        if line.startswith(".. seealso::"):
            index += 1
            while index < len(lines) and (
                not lines[index].strip() or lines[index].startswith(" ")
            ):
                index += 1
            continue
        body.append(_inline(line))
        index += 1
    text = "\n".join(body).strip()
    if fields:
        text += "\n\n" + "\n".join(fields)
    return re.sub(r"\n{3,}", "\n\n", text)


def signature_text(member: Any) -> str:
    """Return a method's signature without ``self``, with readable annotations."""
    # eval_str resolves the string annotations left by
    # "from __future__ import annotations".
    signature = inspect.signature(member, eval_str=True)
    parameters = [p for name, p in signature.parameters.items() if name != "self"]
    return str(signature.replace(parameters=parameters))


def method_reference(cls: type, name: str, member: Any) -> str:
    """Return the Markdown entry for one method."""
    signature = signature_text(member)
    return f"#### `{cls.__name__}.{name}{signature}`\n\n{docstring_markdown(member.__doc__)}\n"


def class_reference(cls: type) -> str:
    """Return the Markdown reference of one client class."""
    methods = public_methods(cls)
    parts = [
        f"### {cls.__name__} ({len(methods)} methods)",
        "",
        docstring_markdown(cls.__doc__),
        "",
    ]
    parts += [method_reference(cls, name, member) for name, member in methods]
    return "\n".join(parts)


def hints_table() -> str:
    """Return the table of method names from other libraries."""
    rows = ["| Client | Name in another library | Use here |", "|---|---|---|"]
    for client, table in (
        ("Jira", _hints.JIRA),
        ("Confluence", _hints.CONFLUENCE),
        ("Bitbucket", _hints.BITBUCKET),
    ):
        for name, targets in table.items():
            use = " or ".join(f"`{target}()`" for target in targets)
            rows.append(f"| {client} | `{name}()` | {use} |")
    return "\n".join(rows)


def errors_list() -> str:
    """Return the exception classes with the first line of their docstrings."""
    classes = [
        member
        for _, member in inspect.getmembers(error, inspect.isclass)
        if issubclass(member, error.APIError)
    ]
    classes.sort(key=lambda cls: (cls is not error.APIError, cls.__name__))
    return "\n".join(
        f"- `{cls.__name__}`: {_inline(inspect.cleandoc(cls.__doc__ or '').splitlines()[0])}"
        for cls in classes
    )


def llms_txt() -> str:
    """Return the content of ``llms.txt``."""
    counts = ", ".join(
        f"{cls.__name__} {len(public_methods(cls))}" for cls in CLIENTS
    )
    return f"""\
# atlassian-api-py

> {SUMMARY}

{FACTS}
## Docs

- [Complete reference in one file]({DOCS}/llms-full.txt): every public method with its signature and docstring ({counts}), examples, errors, and the names used by other libraries
- [Usage guide]({DOCS}/_sources/usage.rst.txt): authentication, Cloud and Data Center differences, common tasks, troubleshooting
- [Coming from atlassian-python-api]({DOCS}/_sources/migration.rst.txt): method mapping tables, behaviour differences, and what this library does not have

## Optional

- [Changelog]({REPO}/blob/main/CHANGELOG.md)
- [Source code]({REPO})
- [API reference as HTML]({DOCS}/atlassian.html)
"""


def llms_full_txt() -> str:
    """Return the content of ``llms-full.txt``."""
    constructor = signature_text(AtlassianAPI.__init__)
    low_level = "\n".join(
        method_reference(AtlassianAPI, name, getattr(AtlassianAPI, name))
        for name in ("get", "post", "put", "delete", "request")
    )
    return f"""\
# atlassian-api-py

> {SUMMARY}

{FACTS}
## Examples

{EXAMPLES}
## Creating a client

`Jira`, `Confluence` and `Bitbucket` take the same arguments:

`{constructor}`

{docstring_markdown(AtlassianAPI.__init__.__doc__)}

A client is also a context manager: `with Jira(url=..., token=...) as jira:` closes its session on exit.

## Errors

{errors_list()}

## Method names from other libraries

These names belong to atlassian-python-api or to the `jira` package and do not exist here. Calling one raises `AttributeError` naming the replacement. Arguments and return values can differ; see [Coming from atlassian-python-api]({DOCS}/migration.html).

{hints_table()}

## Not covered

{NOT_COVERED}
## API reference

{chr(10).join(class_reference(cls) for cls in CLIENTS)}
### Low-level requests (all clients)

{low_level}"""


def write_files(app: Any, exception: Exception | None) -> None:
    """Write both files into the HTML output directory after a build."""
    if exception is not None or app.builder.format != "html":
        return
    outdir = Path(app.outdir)
    (outdir / "llms.txt").write_text(llms_txt(), encoding="utf-8")
    (outdir / "llms-full.txt").write_text(llms_full_txt(), encoding="utf-8")


def setup(app: Any) -> dict[str, bool]:
    """Register the extension with Sphinx."""
    app.connect("build-finished", write_files)
    return {"parallel_read_safe": True, "parallel_write_safe": True}

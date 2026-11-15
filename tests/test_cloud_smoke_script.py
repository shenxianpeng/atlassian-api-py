"""``scripts/cloud_smoke_test.py`` run against a fake Atlassian Cloud site.

The nightly workflow depends on this script, so these tests keep it working:
its exit codes, strict mode, and that ``--seed`` creates exactly what the
read-only checks then need.
"""

import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import responses

SITE = "https://acme.atlassian.net"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cloud_smoke_test.py"
_TRANSPORT_ENV_VARS = (
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)
_SETTINGS = (
    "ATLASSIAN_URL",
    "ATLASSIAN_EMAIL",
    "ATLASSIAN_API_TOKEN",
    "JIRA_PROJECT",
    "JIRA_ISSUE",
    "JIRA_ISSUE_TYPE",
    "CONFLUENCE_SPACE",
    "CONFLUENCE_PAGE_ID",
    "SMOKE_STRICT",
    "SMOKE_TRACEBACK",
    "GITHUB_STEP_SUMMARY",
)


class FakeCloud:
    """A small in-memory Jira and Confluence Cloud site, paging by two."""

    def __init__(self):
        self.issues = []
        self.pages = []
        self.broken = None  # a path suffix that answers 500
        self.writes = []

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _query(request):
        return {k: v[0] for k, v in parse_qs(urlsplit(request.url).query).items()}

    def _issue(self, key):
        return next(i for i in self.issues if i["key"] == key)

    def _page(self, page_id):
        return next(p for p in self.pages if p["id"] == page_id)

    def _cursor_page(self, items, request, path):
        query = self._query(request)
        start = int(query.get("cursor", "0"))
        chunk = items[start : start + 2]
        end = start + len(chunk)
        links = {"next": f"{path}?cursor={end}"} if end < len(items) else {}
        return {"results": chunk, "_links": links}

    # -- routing ---------------------------------------------------------

    def __call__(self, request):
        path = urlsplit(request.url).path
        if self.broken and path.endswith(self.broken):
            return 500, {}, "boom"
        if request.method == "POST" and not path.startswith("/rest/api/2/search"):
            self.writes.append(path)
        for pattern, handler in self.ROUTES:
            match = re.fullmatch(pattern, path)
            if match and handler[0] == request.method:
                result = handler[1](self, request, *match.groups())
                if isinstance(result, tuple):
                    return result
                return 200, {}, json.dumps(result)
        return 404, {}, json.dumps({"message": f"unmocked {request.method} {path}"})

    # -- Jira ------------------------------------------------------------

    def search(self, request):
        body = json.loads(request.body)
        assert body["fields"] == ["*navigable"]
        found = self.issues
        if "labels" in body["jql"]:
            found = [i for i in found if i["fields"]["labels"]]
        start = int(body.get("nextPageToken") or 0)
        end = start + min(body["maxResults"], 2)
        page = {"issues": found[start:end], "isLast": end >= len(found)}
        if not page["isLast"]:
            page["nextPageToken"] = str(end)
        return page

    def create_issue(self, request):
        fields = json.loads(request.body)["fields"]
        assert fields["issuetype"] == {"name": "Task"}
        number = len(self.issues) + 1
        fields["attachment"] = []
        self.issues.append(
            {"id": str(number), "key": f"ABC-{number}", "fields": fields}
        )
        return {"id": str(number), "key": f"ABC-{number}"}

    def attach_to_issue(self, request, key):
        assert request.headers["X-Atlassian-Token"] == "no-check"
        assert b"smoke test fixture" in request.body
        attachment = {"id": "900", "filename": "smoke-test.txt"}
        self._issue(key)["fields"]["attachment"].append(attachment)
        return [attachment]

    # -- Confluence ------------------------------------------------------

    def list_pages(self, request, *_):
        query = self._query(request)
        assert query["status"] == "current"
        found = [p for p in self.pages if query.get("title") in (None, p["title"])]
        return self._cursor_page(found, request, urlsplit(request.url).path)

    def create_page(self, request):
        assert self._query(request) == {"root-level": "true"}
        body = json.loads(request.body)
        page = {
            "id": str(100 + len(self.pages)),
            "title": body["title"],
            "status": "current",
            "body": {"storage": {"value": body["body"]["value"]}},
            "attachments": [],
            "labels": [],
            "comments": [],
        }
        self.pages.append(page)
        return page

    def search_content(self, request):
        assert "start" not in self._query(request)
        return self._cursor_page(self.pages, request, "/rest/api/content/search")

    def page_list(self, request, page_id, kind):
        name = {"footer-comments": "comments"}.get(kind, kind)
        return {"results": self._page(page_id)[name], "_links": {}}

    def attach_to_page(self, request, page_id):
        assert request.headers["X-Atlassian-Token"] == "nocheck"
        self._page(page_id)["attachments"].append(
            {
                "title": "smoke-test.txt",
                "mediaType": "text/plain",
                "downloadLink": f"/download/attachments/{page_id}/smoke-test.txt",
            }
        )
        return {"results": []}

    def label_page(self, request, page_id):
        self._page(page_id)["labels"].append(json.loads(request.body)[0])
        return {"results": []}

    def comment_on_page(self, request):
        body = json.loads(request.body)
        self._page(body["pageId"])["comments"].append({"id": "c1"})
        return {"id": "c1"}

    FILE = (200, {"Content-Type": "text/plain"}, b"fixture")
    ROUTES = [
        (
            r"/rest/api/2/myself",
            ("GET", lambda s, r: {"accountId": "a1", "displayName": "Ada"}),
        ),
        (
            r"/rest/api/2/user",
            ("GET", lambda s, r: {"accountId": s._query(r)["accountId"]}),
        ),
        (r"/rest/api/2/user/search", ("GET", lambda s, r: [{"accountId": "a1"}])),
        (
            r"/rest/api/2/project/search",
            (
                "GET",
                lambda s, r: {"values": [{"key": "ABC", "id": "10"}], "isLast": True},
            ),
        ),
        (r"/rest/api/2/project/ABC", ("GET", lambda s, r: {"key": "ABC", "id": "10"})),
        (r"/rest/api/2/project/ABC/versions", ("GET", lambda s, r: [])),
        (r"/rest/api/2/project/10/components", ("GET", lambda s, r: [])),
        (r"/rest/api/2/search/jql", ("POST", search)),
        (
            r"/rest/api/2/search/approximate-count",
            ("POST", lambda s, r: {"count": len(s.issues)}),
        ),
        (
            r"/rest/api/2/field",
            ("GET", lambda s, r: [{"id": "summary", "name": "Summary"}]),
        ),
        (r"/rest/api/2/issue", ("POST", create_issue)),
        (r"/rest/api/2/issue/([A-Z]+-\d+)", ("GET", lambda s, r, k: s._issue(k))),
        (
            r"/rest/api/2/issue/[A-Z]+-\d+/changelog",
            ("GET", lambda s, r: {"values": [{"id": "h1"}], "isLast": True}),
        ),
        (
            r"/rest/api/2/issue/[A-Z]+-\d+/comment",
            ("GET", lambda s, r: {"comments": []}),
        ),
        (r"/rest/api/2/issue/[A-Z]+-\d+/comment", ("POST", lambda s, r: {"id": "1"})),
        (
            r"/rest/api/2/issue/[A-Z]+-\d+/watchers",
            ("GET", lambda s, r: {"watchers": []}),
        ),
        (
            r"/rest/api/2/issue/[A-Z]+-\d+/transitions",
            ("GET", lambda s, r: {"transitions": []}),
        ),
        (
            r"/rest/api/2/issue/[A-Z]+-\d+/worklog",
            ("GET", lambda s, r: {"worklogs": []}),
        ),
        (r"/rest/api/2/issue/([A-Z]+-\d+)/attachments", ("POST", attach_to_issue)),
        (
            r"/rest/api/2/attachment/900",
            (
                "GET",
                lambda s, r: {
                    "id": "900",
                    "mimeType": "text/plain",
                    "content": f"{SITE}/rest/api/2/attachment/content/900",
                },
            ),
        ),
        (r"/rest/api/2/attachment/content/900", ("GET", lambda s, r: s.FILE)),
        (
            r"/wiki/api/v2/spaces",
            (
                "GET",
                lambda s, r: {"results": [{"id": "98", "key": "DOC"}], "_links": {}},
            ),
        ),
        (r"/wiki/api/v2/spaces/98/pages", ("GET", list_pages)),
        (
            r"/wiki/api/v2/spaces/98/blogposts",
            ("GET", lambda s, r: {"results": [], "_links": {}}),
        ),
        (r"/wiki/api/v2/pages", ("GET", list_pages)),
        (r"/wiki/api/v2/pages", ("POST", create_page)),
        (r"/wiki/api/v2/pages/(\d+)", ("GET", lambda s, r, i: s._page(i))),
        (
            r"/wiki/api/v2/pages/\d+/versions",
            ("GET", lambda s, r: {"results": [{"number": 1}]}),
        ),
        (
            r"/wiki/api/v2/pages/\d+/direct-children",
            ("GET", lambda s, r: {"results": [], "_links": {}}),
        ),
        (
            r"/wiki/api/v2/pages/(\d+)/(attachments|labels|footer-comments)",
            ("GET", page_list),
        ),
        (r"/wiki/rest/api/content/search", ("GET", search_content)),
        (r"/wiki/rest/api/content/(\d+)/child/attachment", ("POST", attach_to_page)),
        (r"/wiki/rest/api/content/(\d+)/label", ("POST", label_page)),
        (r"/wiki/api/v2/footer-comments", ("POST", comment_on_page)),
        (
            r"/wiki/download/attachments/\d+/smoke-test.txt",
            ("GET", lambda s, r: s.FILE),
        ),
    ]


@pytest.fixture
def site(monkeypatch):
    for name in _TRANSPORT_ENV_VARS + _SETTINGS:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.setenv("ATLASSIAN_URL", SITE)
    monkeypatch.setenv("ATLASSIAN_EMAIL", "ada@example.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "token")
    fake = FakeCloud()
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        for method in (responses.GET, responses.POST):
            rsps.add_callback(
                method, re.compile(re.escape(SITE) + "/.*"), callback=fake
            )
        fake.calls = rsps.calls
        yield fake


def run(*args):
    """Load a fresh copy of the script (its results list is global) and run it."""
    spec = importlib.util.spec_from_file_location("cloud_smoke_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main(list(args))


def seed(monkeypatch):
    monkeypatch.setenv("JIRA_PROJECT", "ABC")
    monkeypatch.setenv("CONFLUENCE_SPACE", "DOC")
    return run("--seed")


class TestSettings:
    @pytest.mark.parametrize(
        "name", ["ATLASSIAN_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN"]
    )
    def test_blank_setting_is_reported_as_missing(
        self, site, monkeypatch, capsys, name
    ):
        monkeypatch.setenv(name, "")  # how CI passes a secret that is not set
        assert run() == 2
        assert f"Set {name} " in capsys.readouterr().out
        assert len(site.calls) == 0

    def test_non_cloud_url_is_refused(self, site, monkeypatch, capsys):
        monkeypatch.setenv("ATLASSIAN_URL", "https://jira.company.com")
        assert run() == 2
        assert "not an Atlassian Cloud site" in capsys.readouterr().out

    def test_unknown_argument(self, site, capsys):
        assert run("--write") == 2
        assert "Unknown arguments: --write" in capsys.readouterr().out
        assert len(site.calls) == 0


class TestReadOnlyRun:
    def test_empty_site_passes_with_skips(self, site, capsys):
        assert run() == 0
        out = capsys.readouterr().out
        assert "SKIP  jira.issue(): no issues in the project" in out
        assert "SKIP  confluence page checks: the space has no pages" in out
        assert " 0 failed, 2 skipped" in out
        assert site.writes == []

    def test_strict_fails_an_empty_site(self, site, monkeypatch, capsys):
        monkeypatch.setenv("SMOKE_STRICT", "1")
        assert run() == 1
        assert "skipped checks fail the run" in capsys.readouterr().out

    def test_a_failing_check_exits_1(self, site, capsys):
        site.broken = "/rest/api/2/field"
        assert run() == 1
        out = capsys.readouterr().out
        assert "FAIL  jira.get_fields() / get_field_id(): ServerError" in out
        assert " 1 failed," in out

    def test_step_summary_lists_every_check(self, site, monkeypatch, tmp_path):
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        run()
        text = summary.read_text()
        assert text.startswith("### Cloud smoke test: ")
        assert "| PASS | `jira.get_projects()` | 1 projects |" in text
        assert "| SKIP | `jira.issue()` | no issues in the project |" in text
        assert SITE not in text and "ada@example.com" not in text


class TestSeed:
    @pytest.mark.parametrize("missing", ["JIRA_PROJECT", "CONFLUENCE_SPACE"])
    def test_needs_explicit_project_and_space(self, site, monkeypatch, capsys, missing):
        monkeypatch.setenv("JIRA_PROJECT", "ABC")
        monkeypatch.setenv("CONFLUENCE_SPACE", "DOC")
        monkeypatch.delenv(missing)
        assert run("--seed") == 2
        assert "only writes where you tell it to" in capsys.readouterr().out
        assert len(site.calls) == 0

    def test_creates_fixtures_and_prints_the_pins(self, site, monkeypatch, capsys):
        assert seed(monkeypatch) == 0
        out = capsys.readouterr().out
        assert [i["key"] for i in site.issues] == ["ABC-1", "ABC-2", "ABC-3"]
        assert [i["fields"]["labels"] for i in site.issues] == [
            ["smoke-test-fixture"]
        ] * 3
        assert len(site.issues[0]["fields"]["attachment"]) == 1
        assert [p["title"] for p in site.pages] == [
            f"Smoke test fixture {n}" for n in (1, 2, 3)
        ]
        first = site.pages[0]
        assert (
            len(first["attachments"]),
            len(first["labels"]),
            len(first["comments"]),
        ) == (1, 1, 1)
        assert "gh variable set JIRA_ISSUE --body ABC-1" in out
        assert "gh variable set CONFLUENCE_PAGE_ID --body 100" in out

    def test_second_run_reuses_the_fixtures(self, site, monkeypatch):
        assert seed(monkeypatch) == 0
        site.writes.clear()
        assert seed(monkeypatch) == 0
        assert site.writes == []
        assert (len(site.issues), len(site.pages)) == (3, 3)

    def test_failure_exits_1_without_printing_pins(self, site, monkeypatch, capsys):
        site.broken = "/rest/api/2/issue"
        assert seed(monkeypatch) == 1
        out = capsys.readouterr().out
        assert "FAIL  seed: Jira issues" in out
        assert "gh variable set" not in out

    def test_seeded_site_passes_a_strict_run_with_nothing_skipped(
        self, site, monkeypatch, capsys
    ):
        assert seed(monkeypatch) == 0
        monkeypatch.setenv("JIRA_ISSUE", "ABC-1")
        monkeypatch.setenv("CONFLUENCE_PAGE_ID", "100")
        monkeypatch.setenv("SMOKE_STRICT", "1")
        site.writes.clear()
        capsys.readouterr()
        assert run() == 0
        out = capsys.readouterr().out
        assert " 0 failed, 0 skipped" in out
        assert "PASS  jira.download_attachment(): smoke-test.txt: 7 bytes" in out
        assert "PASS  confluence.download_attachment(): smoke-test.txt: 7 bytes" in out
        assert site.writes == []  # the checks themselves never write

    def test_pins_choose_which_issue_and_page_are_read(self, site, monkeypatch, capsys):
        assert seed(monkeypatch) == 0
        monkeypatch.setenv("JIRA_ISSUE", "ABC-3")  # fixtures without attachments
        monkeypatch.setenv("CONFLUENCE_PAGE_ID", "102")
        capsys.readouterr()
        assert run() == 0
        out = capsys.readouterr().out
        assert "PASS  jira.issue(): ABC-3" in out
        assert "SKIP  jira.download_attachment(): the issue has no attachments" in out
        assert "PASS  confluence: CONFLUENCE_PAGE_ID: page 102" in out
        assert (
            "SKIP  confluence.download_attachment(): the page has no attachments" in out
        )

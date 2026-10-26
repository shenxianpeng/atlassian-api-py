"""Atlassian Cloud behaviour, exercised through a real ``requests`` session.

Endpoint paths and payload shapes follow Atlassian's published OpenAPI specs
for Jira Cloud REST v2 and Confluence Cloud REST v2.
"""

import json

import pytest
import responses
from responses import matchers

from atlassian_api import Bitbucket, Confluence, Jira
from atlassian_api.client import AtlassianAPI, is_cloud_url
from atlassian_api.error import APIError

SITE = "https://acme.atlassian.net"
WIKI = f"{SITE}/wiki"

_TRANSPORT_ENV_VARS = (
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
)


@pytest.fixture
def http(monkeypatch):
    """Intercept HTTP at the transport adapter; unexpected requests fail."""
    for name in _TRANSPORT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    with responses.RequestsMock() as rsps:
        yield rsps


def sent_json(call):
    return json.loads(call.request.body)


# ----------------------------------------------------------------------
# Client
# ----------------------------------------------------------------------


class TestCloudDetection:
    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://acme.atlassian.net", True),
            ("https://ACME.Atlassian.NET/wiki/", True),
            ("https://legacy.jira.com", True),
            ("https://api.atlassian.com/ex/jira/abc-123", True),
            ("https://jira.company.com", False),
            ("https://atlassian.net.evil.example", False),
            ("http://localhost:8080", False),
        ],
    )
    def test_is_cloud_url(self, url, expected):
        assert is_cloud_url(url) is expected

    def test_detected_from_url(self):
        assert AtlassianAPI(url=SITE).cloud is True
        assert AtlassianAPI(url="https://jira.company.com").cloud is False

    def test_explicit_flag_wins(self):
        assert AtlassianAPI(url="https://jira.company.com", cloud=True).cloud is True
        assert AtlassianAPI(url=SITE, cloud=False).cloud is False

    def test_401_with_bearer_token_on_cloud_explains_basic_auth(self, http):
        http.get(f"{SITE}/rest/api/2/myself", status=401, body="Unauthorized")
        with pytest.raises(APIError) as exc:
            AtlassianAPI(url=SITE, token="api-token").get("/rest/api/2/myself")
        assert exc.value.code == 401
        assert exc.value.message.startswith("Unauthorized")
        assert "username=<your account email>" in exc.value.message

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"url": SITE, "username": "me@acme.com", "password": "api-token"},
            {"url": "https://jira.company.com", "token": "pat"},
        ],
    )
    def test_401_without_hint(self, http, kwargs):
        http.get(
            f"{kwargs['url']}/rest/api/2/myself", status=401, body="Unauthorized"
        )
        with pytest.raises(APIError) as exc:
            AtlassianAPI(**kwargs).get("/rest/api/2/myself")
        assert exc.value.message == "Unauthorized"


# ----------------------------------------------------------------------
# Jira Cloud
# ----------------------------------------------------------------------


@pytest.fixture
def jira():
    return Jira(url=SITE, username="me@acme.com", password="api-token")


class TestJiraCloudSearch:
    URL = f"{SITE}/rest/api/2/search/jql"

    def test_follows_next_page_token(self, http, jira):
        http.post(
            self.URL,
            match=[matchers.json_params_matcher({"jql": "project = A", "maxResults": 2, "fields": ["*navigable"]})],
            json={"issues": [{"key": "A-1"}, {"key": "A-2"}], "nextPageToken": "t1"},
        )
        http.post(
            self.URL,
            match=[matchers.json_params_matcher({"jql": "project = A", "maxResults": 2, "fields": ["*navigable"], "nextPageToken": "t1"})],
            json={"issues": [{"key": "A-3"}], "isLast": True},
        )
        issues = jira.search_issue_with_jql("project = A", max_result=2)
        assert [i["key"] for i in issues] == ["A-1", "A-2", "A-3"]

    def test_explicit_fields(self, http, jira):
        http.post(self.URL, json={"issues": [{"key": "A-1"}]})
        jira.search_issue_with_jql("project = A", fields=["summary"])
        assert sent_json(http.calls[0])["fields"] == ["summary"]

    def test_stops_when_token_returns_no_issues(self, http, jira):
        http.post(self.URL, json={"issues": [{"key": "A-1"}], "nextPageToken": "t1"})
        http.post(self.URL, json={"issues": [], "nextPageToken": "t2"})
        assert len(jira.search_issue_with_jql("project = A")) == 1
        assert len(http.calls) == 2

    def test_empty_response(self, http, jira):
        http.post(self.URL, status=200, body="")
        assert jira.search_issue_with_jql("project = A") == []

    def test_server_still_uses_search(self, http):
        http.post(
            "https://jira.company.com/rest/api/2/search",
            json={"total": 1, "maxResults": 50, "issues": [{"key": "A-1"}]},
        )
        server = Jira(url="https://jira.company.com", token="pat")
        assert server.search_issue_with_jql("project = A") == [{"key": "A-1"}]


class TestJiraCloudUsers:
    def test_assign_by_account_id(self, http, jira):
        http.put(f"{SITE}/rest/api/2/issue/A-1/assignee", status=204)
        jira.assign_issue("A-1", "5b10ac8d82e05b22cc7d4ef5")
        assert sent_json(http.calls[0]) == {"accountId": "5b10ac8d82e05b22cc7d4ef5"}

    def test_unassign(self, http, jira):
        http.put(f"{SITE}/rest/api/2/issue/A-1/assignee", status=204)
        jira.assign_issue("A-1")
        assert sent_json(http.calls[0]) == {"accountId": None}

    def test_user_by_account_id(self, http, jira):
        http.get(
            f"{SITE}/rest/api/2/user",
            match=[matchers.query_param_matcher({"accountId": "abc"})],
            json={"accountId": "abc", "displayName": "Ada"},
        )
        assert jira.user("abc").displayName == "Ada"


class TestJiraCloudProjects:
    URL = f"{SITE}/rest/api/2/project/search"

    def test_get_projects_collects_all_pages(self, http, jira):
        http.get(
            self.URL,
            match=[matchers.query_param_matcher({"startAt": "0", "maxResults": "50"})],
            json={"values": [{"key": "A"}, {"key": "B"}], "isLast": False},
        )
        http.get(
            self.URL,
            match=[matchers.query_param_matcher({"startAt": "2", "maxResults": "50"})],
            json={"values": [{"key": "C"}], "isLast": True},
        )
        assert [p.key for p in jira.get_projects()] == ["A", "B", "C"]

    def test_get_projects_empty(self, http, jira):
        http.get(self.URL, json={"values": [], "isLast": False})
        assert jira.get_projects() == []

    def test_create_version_uses_project_id(self, http, jira):
        http.get(f"{SITE}/rest/api/2/project/A", json={"id": "10001", "key": "A"})
        http.post(f"{SITE}/rest/api/2/version", json={"id": "1"})
        jira.create_version("A", "1.0", released=True)
        assert sent_json(http.calls[1]) == {
            "name": "1.0",
            "released": True,
            "projectId": 10001,
        }


# ----------------------------------------------------------------------
# Confluence Cloud (REST API v2)
# ----------------------------------------------------------------------


@pytest.fixture
def confluence():
    return Confluence(url=SITE, username="me@acme.com", password="api-token")


def spaces_lookup(http, key="DOC", space_id="98306"):
    http.get(
        f"{WIKI}/api/v2/spaces",
        match=[matchers.query_param_matcher({"keys": key})],
        json={"results": [{"id": space_id, "key": key}], "_links": {}},
    )


class TestConfluenceCloudSetup:
    def test_wiki_appended_once(self):
        assert Confluence(url=SITE).url == WIKI
        assert Confluence(url=f"{WIKI}/").url == WIKI

    def test_server_url_untouched(self):
        assert Confluence(url="https://wiki.company.com").url == (
            "https://wiki.company.com"
        )


class TestConfluenceCloudPages:
    def test_get_content(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages", json={"results": [{"id": "1"}], "_links": {}})
        result = confluence.get_content()
        assert [p.id for p in result.results] == ["1"]
        assert (result.start, result.limit, result.size) == (0, 25, 1)

    def test_create_page_under_parent(self, http, confluence):
        spaces_lookup(http)
        http.post(f"{WIKI}/api/v2/pages", json={"id": "5"})
        assert confluence.create_content("T", "DOC", "<p>x</p>", ancestors_id=7) == {
            "id": "5"
        }
        assert sent_json(http.calls[1]) == {
            "spaceId": "98306",
            "status": "current",
            "title": "T",
            "parentId": "7",
            "body": {"representation": "storage", "value": "<p>x</p>"},
        }

    def test_create_blogpost(self, http, confluence):
        spaces_lookup(http)
        http.post(f"{WIKI}/api/v2/blogposts", json={"id": "6"})
        confluence.create_content("News", "DOC", "<p>y</p>", type="blogpost")
        assert "parentId" not in sent_json(http.calls[1])

    def test_unsupported_type(self, confluence):
        with pytest.raises(ValueError, match="'comment' is not supported"):
            confluence.create_content("T", "DOC", "x", type="comment")

    def test_update_fetches_current_version(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages/5", json={"id": "5", "version": {"number": 3}})
        http.put(f"{WIKI}/api/v2/pages/5", json={"id": "5"})
        confluence.update_content(5, "T2", "<p>z</p>")
        assert sent_json(http.calls[1]) == {
            "id": "5",
            "status": "current",
            "title": "T2",
            "body": {"representation": "storage", "value": "<p>z</p>"},
            "version": {"number": 4},
        }

    def test_update_with_explicit_version(self, http, confluence):
        http.put(f"{WIKI}/api/v2/blogposts/6", json={"id": "6"})
        confluence.update_content(6, "T", "b", type="blogpost", version=9)
        assert sent_json(http.calls[0])["version"] == {"number": 9}

    def test_update_falls_back_to_version_1(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages/5", status=200, body="")
        http.put(f"{WIKI}/api/v2/pages/5", json={})
        confluence.update_content(5, "T", "b")
        assert sent_json(http.calls[1])["version"] == {"number": 1}

    def test_delete(self, http, confluence):
        http.delete(f"{WIKI}/api/v2/pages/5", status=204)
        assert confluence.delete_content(5) is None

    def test_get_by_id_includes_storage_body(self, http, confluence):
        http.get(
            f"{WIKI}/api/v2/pages/5",
            match=[matchers.query_param_matcher({"body-format": "storage"})],
            json={"id": "5", "body": {"storage": {"value": "<p>x</p>"}}},
        )
        assert confluence.get_content_by_id(5).body.storage.value == "<p>x</p>"

    def test_history(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages/5/versions", json={"results": [{"number": 1}]})
        assert confluence.get_content_history(5).results[0].number == 1

    def test_get_page_by_title(self, http, confluence):
        spaces_lookup(http)
        http.get(
            f"{WIKI}/api/v2/pages",
            match=[
                matchers.query_param_matcher(
                    {"space-id": "98306", "title": "Home", "body-format": "storage"}
                )
            ],
            json={"results": [{"id": "1", "title": "Home"}]},
        )
        assert confluence.get_page_by_title("DOC", "Home").results[0].id == "1"


class TestConfluenceCloudSpaces:
    def test_get_spaces_translates_start_and_limit_to_cursors(self, http, confluence):
        http.get(
            f"{WIKI}/api/v2/spaces",
            match=[matchers.query_param_matcher({"limit": "3"})],
            json={
                "results": [{"key": "A"}, {"key": "B"}],
                "_links": {"next": "/wiki/api/v2/spaces?limit=3&cursor=c1"},
            },
        )
        http.get(
            f"{WIKI}/api/v2/spaces",
            match=[matchers.query_param_matcher({"limit": "3", "cursor": "c1"})],
            json={
                "results": [{"key": "C"}, {"key": "D"}],
                "_links": {"next": "/wiki/api/v2/spaces?limit=3&cursor=c2"},
            },
        )
        result = confluence.get_spaces(start=1, limit=2)
        assert [s.key for s in result.results] == ["B", "C"]
        assert (result.start, result.limit, result.size) == (1, 2, 2)
        assert len(http.calls) == 2

    def test_page_size_is_capped(self, http, confluence):
        http.get(
            f"{WIKI}/api/v2/spaces",
            match=[matchers.query_param_matcher({"limit": "250"})],
            json={"results": []},
        )
        assert confluence.get_spaces(limit=1000).results == []

    def test_non_json_page_ends_listing(self, http, confluence):
        http.get(f"{WIKI}/api/v2/spaces", status=200, body="")
        assert confluence.get_spaces().results == []

    def test_get_space(self, http, confluence):
        spaces_lookup(http)
        assert confluence.get_space("DOC").id == "98306"

    def test_get_space_not_found(self, http, confluence):
        http.get(f"{WIKI}/api/v2/spaces", json={"results": []})
        with pytest.raises(APIError) as exc:
            confluence.get_space("NOPE")
        assert exc.value.code == 404

    def test_space_id_is_cached(self, http, confluence):
        spaces_lookup(http)
        http.get(f"{WIKI}/api/v2/spaces/98306/pages", json={"results": [{"id": "1"}]})
        http.get(f"{WIKI}/api/v2/spaces/98306/blogposts", json={"results": []})
        assert confluence.get_content_by_space("DOC").results[0].id == "1"
        confluence.get_content_by_space("DOC", content_type="blogpost")
        assert len(http.calls) == 3

    def test_child_pages_skip_other_types(self, http, confluence):
        http.get(
            f"{WIKI}/api/v2/pages/5/direct-children",
            json={
                "results": [
                    {"id": "6", "type": "page"},
                    {"id": "7", "type": "whiteboard"},
                    {"id": "8", "type": "page"},
                ]
            },
        )
        assert [p.id for p in confluence.get_child_pages(5).results] == ["6", "8"]


class TestConfluenceCloudExtras:
    def test_attachments(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages/5/attachments", json={"results": [{"id": "a"}]})
        assert confluence.get_attachments(5).results[0].id == "a"

    def test_labels(self, http, confluence):
        http.get(f"{WIKI}/api/v2/pages/5/labels", json={"results": [{"name": "x"}]})
        assert confluence.get_labels(5).results[0].name == "x"

    def test_add_label_still_uses_v1(self, http, confluence):
        http.post(f"{WIKI}/rest/api/content/5/label", json={"results": []})
        confluence.add_label(5, "x")

    def test_search_still_uses_v1(self, http, confluence):
        http.get(f"{WIKI}/rest/api/content/search", json={"results": []})
        assert confluence.search_content("type=page").results == []

    def test_comments(self, http, confluence):
        http.get(
            f"{WIKI}/api/v2/pages/5/footer-comments",
            match=[matchers.query_param_matcher({"body-format": "storage"})],
            json={"results": [{"id": "c"}]},
        )
        assert confluence.get_comments(5).results[0].id == "c"

    def test_add_comment(self, http, confluence):
        http.post(f"{WIKI}/api/v2/footer-comments", json={"id": "c"})
        confluence.add_comment(5, "<p>hi</p>")
        assert sent_json(http.calls[0]) == {
            "pageId": "5",
            "body": {"representation": "storage", "value": "<p>hi</p>"},
        }

    def test_next_cursor_without_links(self):
        assert Confluence._next_cursor(object()) is None


# ----------------------------------------------------------------------
# Bitbucket
# ----------------------------------------------------------------------


class TestBitbucketCloudRejected:
    @pytest.mark.parametrize(
        "url", ["https://bitbucket.org", "https://api.bitbucket.org/2.0"]
    )
    def test_cloud_url_raises(self, url):
        with pytest.raises(ValueError, match="Bitbucket Cloud"):
            Bitbucket(url=url)

    def test_server_url_ok(self):
        assert Bitbucket(url="https://bitbucket.company.com").url == (
            "https://bitbucket.company.com"
        )

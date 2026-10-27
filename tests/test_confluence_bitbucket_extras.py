"""Higher-level Confluence helpers and Bitbucket repository settings/browsing.

Requests go through a real ``requests.Session``; only the transport adapter is
replaced, so URLs, query strings and JSON payloads are checked as sent.
"""

import json
from itertools import islice
from urllib.parse import parse_qs, urlsplit

import pytest
import responses
from responses import matchers

from atlassian_api import Bitbucket, Confluence
from atlassian_api.bitbucket import REPO_PERMISSIONS
from atlassian_api.error import APIError, NotFoundError

WIKI = "https://wiki.company.com"
CLOUD_WIKI = "https://acme.atlassian.net/wiki"
BB = "https://bitbucket.company.com"
REPO = f"{BB}/rest/api/latest/projects/PROJ/repos/repo"

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


def query(params):
    return matchers.query_param_matcher(params)


def body(payload):
    return matchers.json_params_matcher(payload)


def sent_query(call):
    return {k: v[0] for k, v in parse_qs(urlsplit(call.request.url).query).items()}


def sent_path(call):
    return urlsplit(call.request.url).path


# ======================================================================
# Confluence
# ======================================================================


@pytest.fixture
def server():
    return Confluence(WIKI)


@pytest.fixture
def cloud():
    return Confluence("https://acme.atlassian.net")


class TestIterSearch:
    SEARCH = f"{WIKI}/rest/api/content/search"

    def test_single_page_without_next_link(self, http, server):
        http.get(
            self.SEARCH,
            json={"results": [{"id": "1"}, {"id": "2"}]},
            match=[query({"cql": "type = page", "limit": "50"})],
        )
        assert [r.id for r in server.iter_search("type = page")] == ["1", "2"]

    def test_server_follows_start_from_next_link(self, http, server):
        first = {
            "results": [{"id": "1"}],
            "_links": {"next": "/rest/api/content/search?cql=x&start=50&limit=50"},
        }
        second = {
            "results": [{"id": "2"}],
            "_links": {"next": "/rest/api/content/search?cql=x&start=100&limit=50"},
        }
        http.get(self.SEARCH, json=first, match=[query({"cql": "x", "limit": "50"})])
        http.get(
            self.SEARCH,
            json=second,
            match=[query({"cql": "x", "limit": "50", "start": "50"})],
        )
        http.get(
            self.SEARCH,
            json={"results": [{"id": "3"}]},
            match=[query({"cql": "x", "limit": "50", "start": "100"})],
        )
        assert [r.id for r in server.iter_search("x")] == ["1", "2", "3"]

    def test_cloud_follows_cursor_and_replaces_it_each_page(self, http, cloud):
        url = f"{CLOUD_WIKI}/rest/api/content/search"
        link = "/wiki/rest/api/content/search?cql=x&limit=2&cursor={}"
        http.get(
            url,
            json={"results": [{"id": "1"}], "_links": {"next": link.format("c1")}},
            match=[query({"cql": "x", "limit": "2"})],
        )
        http.get(
            url,
            json={"results": [{"id": "2"}], "_links": {"next": link.format("c2")}},
            match=[query({"cql": "x", "limit": "2", "cursor": "c1"})],
        )
        http.get(
            url,
            json={"results": [{"id": "3"}]},
            match=[query({"cql": "x", "limit": "2", "cursor": "c2"})],
        )
        assert [r.id for r in cloud.iter_search("x", page_size=2)] == ["1", "2", "3"]

    def test_stops_when_page_has_next_link_but_no_results(self, http, server):
        http.get(
            self.SEARCH,
            json={"results": [], "_links": {"next": "/s?cql=x&start=50"}},
            match=[query({"cql": "x", "limit": "50"})],  # a 2nd request cannot match
        )
        assert list(server.iter_search("x")) == []
        assert len(http.calls) == 1

    def test_stops_when_next_link_has_no_start_or_cursor(self, http, server):
        # Following such a link would request the same page again, forever.
        http.get(
            self.SEARCH,
            json={"results": [{"id": "1"}], "_links": {"next": "/s?cql=x&limit=50"}},
        )
        # islice: a regression would loop forever instead of failing.
        assert [r.id for r in islice(server.iter_search("x"), 5)] == ["1"]
        assert len(http.calls) == 1

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"body": ""},
            {"body": "not json", "content_type": "text/plain"},
            {"json": ["not", "an", "object"]},
        ],
        ids=["empty", "plain-text", "json-list"],
    )
    def test_stops_on_response_that_is_not_a_json_object(self, http, server, kwargs):
        http.get(self.SEARCH, **kwargs)
        assert list(server.iter_search("x")) == []

    def test_response_without_results_key_yields_nothing(self, http, server):
        http.get(self.SEARCH, json={"size": 0})
        assert list(server.iter_search("x")) == []

    def test_html_login_page_raises(self, http, server):
        http.get(self.SEARCH, body="<html>login</html>", content_type="text/html")
        with pytest.raises(APIError):
            list(server.iter_search("x"))

    def test_is_lazy(self, http, server):
        http.get(
            self.SEARCH,
            json={
                "results": [{"id": "1"}, {"id": "2"}],
                "_links": {"next": "/s?cql=x&start=2"},
            },
            match=[query({"cql": "x", "limit": "50"})],
        )
        http.get(
            self.SEARCH,
            json={"results": [{"id": "3"}]},
            match=[query({"cql": "x", "limit": "50", "start": "2"})],
        )
        results = server.iter_search("x")
        assert len(http.calls) == 0  # nothing is requested until iterated
        assert next(results).id == "1"
        assert next(results).id == "2"
        assert len(http.calls) == 1  # the next page is not fetched early
        assert next(results).id == "3"
        assert len(http.calls) == 2
        assert next(results, None) is None


class TestCreateOrUpdatePage:
    CONTENT = f"{WIKI}/rest/api/content"
    LOOKUP = {"spaceKey": "DOC", "title": "Report", "type": "page"}
    STORAGE = {"storage": {"value": "<p>hi</p>", "representation": "storage"}}

    def test_server_updates_existing_page_with_incremented_version(self, http, server):
        http.get(
            self.CONTENT, json={"results": [{"id": "42"}]}, match=[query(self.LOOKUP)]
        )
        http.get(
            f"{self.CONTENT}/42",
            json={"version": {"number": 3}},
            match=[query({"expand": "version"})],
        )
        http.put(
            f"{self.CONTENT}/42",
            json={"id": "42"},
            match=[
                body(
                    {
                        "version": {"number": 4},
                        "title": "Report",
                        "type": "page",
                        "body": self.STORAGE,
                    }
                )
            ],
        )
        assert server.create_or_update_page("DOC", "Report", "<p>hi</p>", 7) == {
            "id": "42"
        }
        assert [c.request.method for c in http.calls] == ["GET", "GET", "PUT"]

    @pytest.mark.parametrize("parent_id, ancestors", [(None, None), (7, [{"id": 7}])])
    def test_server_creates_page_when_title_is_unknown(
        self, http, server, parent_id, ancestors
    ):
        http.get(self.CONTENT, json={"results": []}, match=[query(self.LOOKUP)])
        payload = {
            "type": "page",
            "title": "Report",
            "space": {"key": "DOC"},
            "body": self.STORAGE,
        }
        if ancestors:
            payload["ancestors"] = ancestors
        http.post(self.CONTENT, json={"id": "99"}, match=[body(payload)])
        result = server.create_or_update_page(
            "DOC", "Report", "<p>hi</p>", parent_id=parent_id
        )
        assert result == {"id": "99"}

    def test_server_creates_page_when_lookup_returns_empty_body(self, http, server):
        http.get(self.CONTENT, body="", match=[query(self.LOOKUP)])
        http.post(self.CONTENT, json={"id": "99"})
        assert server.create_or_update_page("DOC", "Report", "<p>hi</p>") == {
            "id": "99"
        }

    def test_server_existing_page_is_not_moved_under_new_parent(self, http, server):
        http.get(self.CONTENT, json={"results": [{"id": "42"}]})
        http.get(f"{self.CONTENT}/42", json={"version": {"number": 1}})
        http.put(f"{self.CONTENT}/42", json={})
        server.create_or_update_page("DOC", "Report", "<p>hi</p>", parent_id=7)
        assert "ancestors" not in json.loads(http.calls[-1].request.body)

    def _cloud_space_lookup(self, http):
        http.get(
            f"{CLOUD_WIKI}/api/v2/spaces",
            json={"results": [{"id": "100", "key": "DOC"}]},
            match=[query({"keys": "DOC"})],
        )

    def _cloud_page_lookup(self, http, results):
        http.get(
            f"{CLOUD_WIKI}/api/v2/pages",
            json={"results": results},
            match=[
                query(
                    {
                        "space-id": "100",
                        "title": "Report",
                        # Archived pages with the same title are not updated.
                        "status": "current",
                        "body-format": "storage",
                        "limit": "25",
                    }
                )
            ],
        )

    def test_cloud_updates_existing_page_through_v2(self, http, cloud):
        self._cloud_space_lookup(http)
        self._cloud_page_lookup(http, [{"id": "55"}])
        http.get(f"{CLOUD_WIKI}/api/v2/pages/55", json={"version": {"number": 2}})
        http.put(
            f"{CLOUD_WIKI}/api/v2/pages/55",
            json={"id": "55"},
            match=[
                body(
                    {
                        "id": "55",
                        "status": "current",
                        "title": "Report",
                        "body": {"representation": "storage", "value": "<p>hi</p>"},
                        "version": {"number": 3},
                    }
                )
            ],
        )
        assert cloud.create_or_update_page("DOC", "Report", "<p>hi</p>") == {"id": "55"}

    @pytest.mark.parametrize("parent_id, extra", [(None, {}), (9, {"parentId": "9"})])
    def test_cloud_creates_page_with_parent_id(self, http, cloud, parent_id, extra):
        self._cloud_space_lookup(http)
        self._cloud_page_lookup(http, [])
        http.post(
            f"{CLOUD_WIKI}/api/v2/pages",
            json={"id": "77"},
            match=[
                body(
                    {
                        "spaceId": "100",
                        "status": "current",
                        "title": "Report",
                        "body": {"representation": "storage", "value": "<p>hi</p>"},
                        **extra,
                    }
                )
            ],
        )
        result = cloud.create_or_update_page(
            "DOC", "Report", "<p>hi</p>", parent_id=parent_id
        )
        assert result == {"id": "77"}
        # The space key is resolved once and reused for lookup and creation.
        spaces = [c for c in http.calls if sent_path(c).endswith("/api/v2/spaces")]
        assert len(spaces) == 1


class TestDownloadAttachment:
    LISTING = f"{WIKI}/rest/api/content/5/child/attachment"
    LINK = "/download/attachments/5/a.txt?version=1&api=v2"
    LINK_QUERY = {"version": "1", "api": "v2"}

    def test_server_returns_bytes_from_relative_download_link(self, http, server):
        http.get(
            self.LISTING,
            json={"results": [{"_links": {"download": self.LINK}}]},
            match=[query({"filename": "a.txt"})],
        )
        http.get(
            f"{WIKI}/download/attachments/5/a.txt",
            body=b"hello",
            match=[query(self.LINK_QUERY)],
        )
        assert server.download_attachment(5, "a.txt") == b"hello"

    def test_server_download_link_keeps_the_context_path(self, http):
        confluence = Confluence(f"{WIKI}/confluence")
        http.get(
            f"{WIKI}/confluence/rest/api/content/5/child/attachment",
            json={"results": [{"_links": {"download": self.LINK}}]},
        )
        http.get(f"{WIKI}/confluence/download/attachments/5/a.txt", body=b"ctx")
        assert confluence.download_attachment(5, "a.txt") == b"ctx"

    def test_server_filename_is_sent_url_encoded(self, http, server):
        http.get(
            self.LISTING,
            json={"results": [{"_links": {"download": self.LINK}}]},
            match=[query({"filename": "my report & more.txt"})],
        )
        http.get(f"{WIKI}/download/attachments/5/a.txt", body=b"x")
        server.download_attachment(5, "my report & more.txt")
        assert "my+report+%26+more.txt" in http.calls[0].request.url

    def test_cloud_uses_download_link_relative_to_wiki(self, http, cloud):
        http.get(
            f"{CLOUD_WIKI}/api/v2/pages/5/attachments",
            json={"results": [{"downloadLink": self.LINK}]},
            match=[query({"filename": "a.txt"})],
        )
        http.get(
            f"{CLOUD_WIKI}/download/attachments/5/a.txt",
            body=b"cloud",
            match=[query(self.LINK_QUERY)],
        )
        assert cloud.download_attachment(5, "a.txt") == b"cloud"

    @pytest.mark.parametrize(
        "item",
        [
            {
                "_links": {"download": "/download/attachments/5/a.pdf"},
                "extensions": {"mediaType": "application/pdf"},
            },
            {
                "downloadLink": "/download/attachments/5/a.pdf",
                "mediaType": "application/pdf",
            },
        ],
    )
    def test_login_page_instead_of_file_raises(self, http, server, cloud, item):
        client = cloud if "downloadLink" in item else server
        listing = (
            f"{CLOUD_WIKI}/api/v2/pages/5/attachments"
            if client is cloud
            else self.LISTING
        )
        http.get(listing, json={"results": [item]})
        http.get(
            f"{client.url}/download/attachments/5/a.pdf",
            body="<html>Login</html>",
            content_type="text/html",
        )
        with pytest.raises(APIError, match="HTML page"):
            client.download_attachment(5, "a.pdf")

    @pytest.mark.parametrize("as_str", [False, True])
    def test_streams_to_path_and_returns_it(self, http, server, tmp_path, as_str):
        data = bytes(range(256)) * 1000  # larger than one 64 KiB chunk
        http.get(
            self.LISTING,
            json={"results": [{"_links": {"download": self.LINK}}]},
        )
        http.get(f"{WIKI}/download/attachments/5/a.txt", body=data)
        target = tmp_path / "out.bin"
        result = server.download_attachment(
            5, "a.txt", path=str(target) if as_str else target
        )
        assert result == target
        assert target.read_bytes() == data

    def test_takes_the_first_matching_attachment(self, http, server):
        links = [{"_links": {"download": self.LINK}}, {"_links": {"download": "/x"}}]
        http.get(self.LISTING, json={"results": links})
        http.get(f"{WIKI}/download/attachments/5/a.txt", body=b"first")
        assert server.download_attachment(5, "a.txt") == b"first"

    @pytest.mark.parametrize(
        "client, listing",
        [
            ("server", f"{WIKI}/rest/api/content/5/child/attachment"),
            ("cloud", f"{CLOUD_WIKI}/api/v2/pages/5/attachments"),
        ],
    )
    @pytest.mark.parametrize("payload", [{"results": []}, {}, None])
    def test_missing_attachment_raises_not_found(
        self, http, request, client, listing, payload
    ):
        http.get(listing, json=payload, match=[query({"filename": "gone.txt"})])
        with pytest.raises(NotFoundError) as exc:
            request.getfixturevalue(client).download_attachment(5, "gone.txt")
        assert exc.value.code == 404
        assert "gone.txt" in exc.value.message

    @pytest.mark.parametrize(
        "client, listing, attachment",
        [
            ("server", LISTING, {"_links": {}}),
            ("server", LISTING, {"_links": {"download": ""}}),
            ("server", LISTING, {"title": "no links at all"}),
            ("cloud", f"{CLOUD_WIKI}/api/v2/pages/5/attachments", {"downloadLink": ""}),
            ("cloud", f"{CLOUD_WIKI}/api/v2/pages/5/attachments", {"title": "x"}),
        ],
    )
    def test_attachment_without_link_raises_api_error(
        self, http, request, client, listing, attachment
    ):
        http.get(listing, json={"results": [attachment]})
        with pytest.raises(APIError) as exc:
            request.getfixturevalue(client).download_attachment(5, "a.txt")
        assert not isinstance(exc.value, NotFoundError)
        assert "no download link" in exc.value.message

    def test_download_link_to_another_host_is_refused(self, http, server):
        evil = "https://evil.example/download/a.txt"
        http.get(self.LISTING, json={"results": [{"_links": {"download": evil}}]})
        with pytest.raises(ValueError):
            server.download_attachment(5, "a.txt")
        assert len(http.calls) == 1  # credentials never left the listing request


class TestExportPagePdf:
    EXPORT = f"{WIKI}/spaces/flyingpdf/pdfpageexport.action"
    PDF = b"%PDF-1.4 fake"

    def test_returns_pdf_bytes(self, http, server):
        http.get(
            self.EXPORT,
            body=self.PDF,
            content_type="application/pdf",
            match=[query({"pageId": "123"})],
        )
        assert server.export_page_pdf(123) == self.PDF

    def test_saves_pdf_to_path(self, http, server, tmp_path):
        http.get(self.EXPORT, body=self.PDF, content_type="application/pdf")
        target = tmp_path / "page.pdf"
        assert server.export_page_pdf("123", path=target) == target
        assert target.read_bytes() == self.PDF

    def test_html_response_is_a_login_page_not_a_pdf(self, http, server):
        http.get(self.EXPORT, body="<html>Log in</html>", content_type="text/html")
        with pytest.raises(APIError) as exc:
            server.export_page_pdf(123)
        assert "HTML page" in exc.value.message

    def test_html_response_does_not_create_the_file(self, http, server, tmp_path):
        http.get(
            self.EXPORT,
            body="<html>SSO</html>",
            content_type="text/html; charset=utf-8",
        )
        target = tmp_path / "page.pdf"
        with pytest.raises(APIError):
            server.export_page_pdf(123, path=target)
        assert not target.exists()

    def test_http_error_propagates(self, http, server):
        http.get(self.EXPORT, status=404, body="no such page")
        with pytest.raises(NotFoundError):
            server.export_page_pdf(123)

    def test_cloud_is_not_supported_and_makes_no_request(self, http, cloud, tmp_path):
        with pytest.raises(NotImplementedError, match="Cloud"):
            cloud.export_page_pdf(123, path=tmp_path / "page.pdf")
        assert len(http.calls) == 0
        assert not (tmp_path / "page.pdf").exists()


# ======================================================================
# Bitbucket Server
# ======================================================================


@pytest.fixture
def bb():
    return Bitbucket(BB)


def page(values, last=True, next_start=None):
    payload = {"values": values, "isLastPage": last}
    if next_start is not None:
        payload["nextPageStart"] = next_start
    return payload


class TestDefaultBranch:
    BRANCH = {"id": "refs/heads/main", "displayId": "main"}

    def test_uses_default_branch_endpoint(self, http, bb):
        http.get(f"{REPO}/default-branch", json=self.BRANCH)
        assert bb.get_default_branch("PROJ", "repo").displayId == "main"
        assert len(http.calls) == 1

    def test_falls_back_to_branches_default_on_404(self, http, bb):
        http.get(f"{REPO}/default-branch", status=404, body="not found")
        http.get(f"{REPO}/branches/default", json=self.BRANCH)
        assert bb.get_default_branch("PROJ", "repo").id == "refs/heads/main"

    def test_missing_repository_raises_when_fallback_is_404_too(self, http, bb):
        http.get(f"{REPO}/default-branch", status=404)
        http.get(f"{REPO}/branches/default", status=404)
        with pytest.raises(NotFoundError):
            bb.get_default_branch("PROJ", "repo")

    @pytest.mark.parametrize("status", [400, 401, 403, 500])
    def test_other_errors_propagate_without_fallback(self, http, bb, status):
        http.get(f"{REPO}/default-branch", status=status, body="boom")
        with pytest.raises(APIError) as exc:
            bb.get_default_branch("PROJ", "repo")
        assert exc.value.code == status
        assert len(http.calls) == 1


class TestWebhooks:
    HOOKS = f"{REPO}/webhooks"

    def test_get_webhooks_follows_pages(self, http, bb):
        http.get(
            self.HOOKS,
            json=page([{"id": 1}], last=False, next_start=1),
            match=[query({})],
        )
        http.get(self.HOOKS, json=page([{"id": 2}]), match=[query({"start": "1"})])
        assert [h.id for h in bb.get_webhooks("PROJ", "repo")] == [1, 2]

    def test_get_webhooks_limit_caps_total_and_shrinks_next_request(self, http, bb):
        http.get(
            self.HOOKS,
            json=page([{"id": 1}, {"id": 2}], last=False, next_start=2),
            match=[query({"limit": "3"})],
        )
        http.get(
            self.HOOKS,
            json=page([{"id": 3}, {"id": 4}], last=False, next_start=4),
            match=[query({"limit": "1", "start": "2"})],
        )
        assert [h.id for h in bb.get_webhooks("PROJ", "repo", limit=3)] == [1, 2, 3]

    def test_get_webhooks_empty(self, http, bb):
        http.get(self.HOOKS, json=page([]))
        assert bb.get_webhooks("PROJ", "repo") == []

    def test_create_webhook_posts_payload_with_active_by_default(self, http, bb):
        events = ["repo:refs_changed", "pr:opened"]
        http.post(
            self.HOOKS,
            json={"id": 9},
            match=[
                body(
                    {
                        "name": "CI",
                        "url": "https://ci.example.com/hook",
                        "events": events,
                        "active": True,
                    }
                )
            ],
        )
        result = bb.create_webhook(
            "PROJ", "repo", "CI", "https://ci.example.com/hook", events
        )
        assert result == {"id": 9}

    def test_create_webhook_can_be_inactive(self, http, bb):
        http.post(self.HOOKS, json={"id": 9})
        bb.create_webhook(
            "PROJ", "repo", "CI", "https://x", ["pr:opened"], active=False
        )
        assert json.loads(http.calls[0].request.body)["active"] is False

    @pytest.mark.parametrize("webhook_id", [9, "9"])
    def test_delete_webhook(self, http, bb, webhook_id):
        http.delete(f"{self.HOOKS}/9", status=204)
        assert bb.delete_webhook("PROJ", "repo", webhook_id) is None
        assert http.calls[0].request.method == "DELETE"

    def test_delete_unknown_webhook_raises(self, http, bb):
        http.delete(f"{self.HOOKS}/9", status=404)
        with pytest.raises(NotFoundError):
            bb.delete_webhook("PROJ", "repo", 9)


class TestRepoPermissions:
    @pytest.mark.parametrize("principal", ["users", "groups"])
    def test_get_repo_permissions_for_principal(self, http, bb, principal):
        entries = [{"permission": "REPO_READ"}, {"permission": "REPO_ADMIN"}]
        http.get(f"{REPO}/permissions/{principal}", json=page(entries))
        result = bb.get_repo_permissions("PROJ", "repo", principal=principal)
        assert [e.permission for e in result] == ["REPO_READ", "REPO_ADMIN"]

    def test_get_repo_permissions_defaults_to_users_and_honours_limit(self, http, bb):
        http.get(
            f"{REPO}/permissions/users",
            json=page([{"permission": "REPO_READ"}]),
            match=[query({"limit": "10"})],
        )
        assert len(bb.get_repo_permissions("PROJ", "repo", limit=10)) == 1

    def test_get_repo_permissions_follows_pages(self, http, bb):
        url = f"{REPO}/permissions/groups"
        http.get(
            url, json=page([{"n": 1}], last=False, next_start=1), match=[query({})]
        )
        http.get(url, json=page([{"n": 2}]), match=[query({"start": "1"})])
        assert len(bb.get_repo_permissions("PROJ", "repo", "groups")) == 2

    @pytest.mark.parametrize("principal", ["users", "groups"])
    @pytest.mark.parametrize("permission", REPO_PERMISSIONS)
    def test_set_repo_permission_sends_name_and_permission_as_query(
        self, http, bb, principal, permission
    ):
        http.put(
            f"{REPO}/permissions/{principal}",
            status=204,
            match=[query({"name": "jdoe", "permission": permission})],
        )
        assert (
            bb.set_repo_permission("PROJ", "repo", "jdoe", permission, principal)
            is None
        )

    def test_set_repo_permission_defaults_to_users(self, http, bb):
        http.put(f"{REPO}/permissions/users", status=204)
        bb.set_repo_permission("PROJ", "repo", "jdoe", "REPO_WRITE")
        assert sent_path(http.calls[0]).endswith("/permissions/users")

    def test_set_repo_permission_encodes_group_names(self, http, bb):
        http.put(f"{REPO}/permissions/groups", status=204)
        bb.set_repo_permission("PROJ", "repo", "dev team&ops", "REPO_READ", "groups")
        assert sent_query(http.calls[0])["name"] == "dev team&ops"

    @pytest.mark.parametrize(
        "permission", ["repo_read", "REPO_READ ", "PROJECT_READ", "ADMIN", ""]
    )
    def test_set_repo_permission_rejects_unknown_permission(self, http, bb, permission):
        with pytest.raises(ValueError, match="Unknown permission"):
            bb.set_repo_permission("PROJ", "repo", "jdoe", permission)
        assert len(http.calls) == 0

    @pytest.mark.parametrize("principal", ["user", "Users", "teams", ""])
    def test_invalid_principal_is_rejected_before_any_request(
        self, http, bb, principal
    ):
        with pytest.raises(ValueError, match="principal"):
            bb.get_repo_permissions("PROJ", "repo", principal=principal)
        with pytest.raises(ValueError, match="principal"):
            bb.set_repo_permission("PROJ", "repo", "jdoe", "REPO_READ", principal)
        with pytest.raises(ValueError, match="principal"):
            bb.revoke_repo_permission("PROJ", "repo", "jdoe", principal)
        assert len(http.calls) == 0

    @pytest.mark.parametrize("principal", ["users", "groups"])
    def test_revoke_repo_permission_sends_name_only(self, http, bb, principal):
        http.delete(
            f"{REPO}/permissions/{principal}",
            status=204,
            match=[query({"name": "jdoe"})],
        )
        assert bb.revoke_repo_permission("PROJ", "repo", "jdoe", principal) is None

    def test_revoke_repo_permission_defaults_to_users(self, http, bb):
        http.delete(f"{REPO}/permissions/users", status=204)
        bb.revoke_repo_permission("PROJ", "repo", "jdoe")
        assert http.calls[0].request.method == "DELETE"

    def test_permission_errors_propagate(self, http, bb):
        http.put(f"{REPO}/permissions/users", status=403, body="no")
        with pytest.raises(APIError) as exc:
            bb.set_repo_permission("PROJ", "repo", "jdoe", "REPO_ADMIN")
        assert exc.value.code == 403


class TestListFiles:
    FILES = f"{REPO}/files"

    def test_lists_repository_root(self, http, bb):
        http.get(self.FILES, json=page(["README.md", "src/a.py"]), match=[query({})])
        assert bb.list_files("PROJ", "repo") == ["README.md", "src/a.py"]

    def test_path_is_stripped_of_slashes_and_quoted(self, http, bb):
        http.get(f"{self.FILES}/src/my%20dir", json=page(["a.py"]))
        assert bb.list_files("PROJ", "repo", path="/src/my dir/") == ["a.py"]
        assert (
            sent_path(http.calls[0])
            == "/rest/api/latest/projects/PROJ/repos/repo/files/src/my%20dir"
        )

    def test_special_characters_in_path_cannot_alter_the_query(self, http, bb):
        http.get(f"{self.FILES}/a%3Fb%23c", json=page([]))
        bb.list_files("PROJ", "repo", path="a?b#c")
        assert sent_query(http.calls[0]) == {}

    def test_at_and_limit_are_sent_only_when_given(self, http, bb):
        http.get(
            f"{self.FILES}/src",
            json=page(["a.py"]),
            match=[query({"at": "refs/heads/dev", "limit": "5"})],
        )
        assert bb.list_files("PROJ", "repo", "src", at="refs/heads/dev", limit=5) == [
            "a.py"
        ]

    def test_at_only(self, http, bb):
        http.get(self.FILES, json=page(["a"]), match=[query({"at": "v1.0"})])
        assert bb.list_files("PROJ", "repo", at="v1.0") == ["a"]

    def test_follows_pages_and_keeps_at(self, http, bb):
        http.get(
            self.FILES,
            json=page(["a"], last=False, next_start=1),
            match=[query({"at": "v1"})],
        )
        http.get(
            self.FILES, json=page(["b"]), match=[query({"at": "v1", "start": "1"})]
        )
        assert bb.list_files("PROJ", "repo", at="v1") == ["a", "b"]

    def test_limit_truncates_an_oversized_page(self, http, bb):
        http.get(self.FILES, json=page(["a", "b", "c"]), match=[query({"limit": "2"})])
        assert bb.list_files("PROJ", "repo", limit=2) == ["a", "b"]

    def test_empty_repository(self, http, bb):
        http.get(self.FILES, json=page([]))
        assert bb.list_files("PROJ", "repo") == []


class TestCompare:
    @pytest.mark.parametrize(
        "method, endpoint",
        [("compare_commits", "commits"), ("compare_changes", "changes")],
    )
    def test_sends_from_and_to_refs(self, http, bb, method, endpoint):
        values = [{"id": "abc"}]
        http.get(
            f"{REPO}/compare/{endpoint}",
            json=page(values),
            match=[query({"from": "feature/x", "to": "main"})],
        )
        result = getattr(bb, method)("PROJ", "repo", "feature/x", "main")
        assert [v.id for v in result] == ["abc"]

    @pytest.mark.parametrize(
        "method, endpoint",
        [("compare_commits", "commits"), ("compare_changes", "changes")],
    )
    def test_limit_and_pagination(self, http, bb, method, endpoint):
        url = f"{REPO}/compare/{endpoint}"
        http.get(
            url,
            json=page([{"n": 1}, {"n": 2}], last=False, next_start=2),
            match=[query({"from": "a", "to": "b", "limit": "3"})],
        )
        http.get(
            url,
            json=page([{"n": 3}]),
            match=[query({"from": "a", "to": "b", "limit": "1", "start": "2"})],
        )
        result = getattr(bb, method)("PROJ", "repo", "a", "b", limit=3)
        assert [v.n for v in result] == [1, 2, 3]

    @pytest.mark.parametrize("method", ["compare_commits", "compare_changes"])
    def test_identical_refs_give_empty_list(self, http, bb, method):
        http.get(f"{REPO}/compare/{method.split('_')[1]}", json=page([]))
        assert getattr(bb, method)("PROJ", "repo", "main", "main") == []

    @pytest.mark.parametrize("method", ["compare_commits", "compare_changes"])
    def test_unknown_ref_raises_not_found(self, http, bb, method):
        http.get(f"{REPO}/compare/{method.split('_')[1]}", status=404, body="no ref")
        with pytest.raises(NotFoundError):
            getattr(bb, method)("PROJ", "repo", "nope", "main")


@pytest.mark.parametrize("root", ["", "/", "//"])
def test_list_files_root_has_no_trailing_slash(root):
    with responses.RequestsMock() as rsps:
        rsps.get(
            "https://bitbucket.company.com/rest/api/latest/projects/P/repos/r/files",
            json={"values": ["a.py"], "isLastPage": True},
        )
        bb = Bitbucket(url="https://bitbucket.company.com", token="t")
        assert bb.list_files("P", "r", path=root) == ["a.py"]
        assert rsps.calls[0].request.url.split("?")[0].endswith("/files")

"""Jira search, field, user, worklog and attachment helpers.

Requests go through a real ``requests`` session; ``responses`` fakes only the
transport, so payloads, query strings and headers are checked as sent.
"""

import json

import pytest
import responses
from responses import matchers

from atlassian_api import Jira
from atlassian_api.error import APIError

SERVER = "https://jira.company.com"
CLOUD = "https://acme.atlassian.net"


@pytest.fixture
def http(monkeypatch):
    """Intercept HTTP at the transport adapter; unexpected requests fail."""
    for name in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTP_PROXY", "HTTPS_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def server():
    return Jira(url=SERVER, token="pat")


@pytest.fixture
def cloud():
    return Jira(url=CLOUD, username="me@acme.com", password="api-token")


@pytest.fixture(params=["server", "cloud"])
def jira(request):
    """The same client on both deployments, for behaviour that must not differ."""
    return request.getfixturevalue(request.param)


def sent_json(call):
    return json.loads(call.request.body)


def issues(*keys):
    return [{"key": key} for key in keys]


# ----------------------------------------------------------------------
# Searching
# ----------------------------------------------------------------------


class TestIterIssuesServer:
    URL = f"{SERVER}/rest/api/2/search"

    def test_pages_with_start_at_until_total_reached(self, http, server):
        for start_at, page in [(0, ("A-1", "A-2")), (2, ("A-3", "A-4")), (4, ("A-5",))]:
            http.post(
                self.URL,
                match=[
                    matchers.json_params_matcher(
                        {"jql": "project = A", "startAt": start_at, "maxResults": 2}
                    )
                ],
                json={"total": 5, "issues": issues(*page)},
            )
        keys = [i["key"] for i in server.iter_issues("project = A", page_size=2)]
        assert keys == ["A-1", "A-2", "A-3", "A-4", "A-5"]
        assert len(http.calls) == 3

    def test_start_at_advances_by_issues_received_not_page_size(self, http, server):
        # Jira may return fewer issues than requested (e.g. permission filtering).
        http.post(self.URL, json={"total": 3, "issues": issues("A-1")})
        http.post(self.URL, json={"total": 3, "issues": issues("A-2", "A-3")})
        assert len(list(server.iter_issues("x", page_size=50))) == 3
        assert [sent_json(c)["startAt"] for c in http.calls] == [0, 1]

    def test_fields_sent_only_when_given(self, http, server):
        http.post(self.URL, json={"total": 1, "issues": issues("A-1")})
        http.post(self.URL, json={"total": 1, "issues": issues("A-1")})
        list(server.iter_issues("x"))
        list(server.iter_issues("x", fields=["summary", "status"]))
        assert "fields" not in sent_json(http.calls[0])
        assert sent_json(http.calls[1])["fields"] == ["summary", "status"]
        assert sent_json(http.calls[0])["maxResults"] == 100  # default page size

    def test_empty_page_stops_even_if_total_claims_more(self, http, server):
        http.post(self.URL, json={"total": 10, "issues": issues("A-1")})
        http.post(self.URL, json={"total": 10, "issues": []})
        assert len(list(server.iter_issues("x"))) == 1
        assert len(http.calls) == 2

    def test_missing_total_ends_after_first_page(self, http, server):
        http.post(self.URL, json={"issues": issues("A-1", "A-2")})
        assert len(list(server.iter_issues("x"))) == 2
        assert len(http.calls) == 1

    @pytest.mark.parametrize("response", [{"body": ""}, {"json": {}}, {"json": None}])
    def test_empty_response_yields_nothing(self, http, server, response):
        http.post(self.URL, status=200, **response)
        assert list(server.iter_issues("x")) == []

    def test_is_lazy(self, http, server):
        http.post(self.URL, json={"total": 4, "issues": issues("A-1", "A-2")})
        gen = server.iter_issues("x", page_size=2)
        assert len(http.calls) == 0  # nothing is sent until iteration starts
        assert next(gen) == {"key": "A-1"}
        assert next(gen) == {"key": "A-2"}
        assert len(http.calls) == 1  # the second page is not fetched yet


class TestIterIssuesCloud:
    URL = f"{CLOUD}/rest/api/2/search/jql"

    def test_default_fields_are_navigable(self, http, cloud):
        http.post(
            self.URL,
            match=[
                matchers.json_params_matcher(
                    {"jql": "project = A", "maxResults": 100, "fields": ["*navigable"]}
                )
            ],
            json={"issues": issues("A-1"), "isLast": True},
        )
        assert list(cloud.iter_issues("project = A")) == issues("A-1")

    def test_follows_token_and_keeps_other_payload(self, http, cloud):
        http.post(self.URL, json={"issues": issues("A-1"), "nextPageToken": "t1"})
        http.post(self.URL, json={"issues": issues("A-2"), "nextPageToken": "t2"})
        http.post(self.URL, json={"issues": issues("A-3"), "isLast": True})
        got = list(cloud.iter_issues("x", fields=["summary"], page_size=1))
        assert [i["key"] for i in got] == ["A-1", "A-2", "A-3"]
        payloads = [sent_json(c) for c in http.calls]
        assert "nextPageToken" not in payloads[0]
        assert [p.get("nextPageToken") for p in payloads[1:]] == ["t1", "t2"]
        assert all(p["fields"] == ["summary"] for p in payloads)

    def test_is_last_wins_over_a_token(self, http, cloud):
        http.post(
            self.URL,
            json={"issues": issues("A-1"), "isLast": True, "nextPageToken": "t1"},
        )
        assert len(list(cloud.iter_issues("x"))) == 1
        assert len(http.calls) == 1

    def test_missing_token_ends_listing(self, http, cloud):
        http.post(self.URL, json={"issues": issues("A-1", "A-2")})
        assert len(list(cloud.iter_issues("x"))) == 2
        assert len(http.calls) == 1

    def test_empty_page_with_token_ends_listing(self, http, cloud):
        http.post(self.URL, json={"issues": [], "nextPageToken": "again"})
        assert list(cloud.iter_issues("x")) == []
        assert len(http.calls) == 1

    def test_empty_response_yields_nothing(self, http, cloud):
        http.post(self.URL, status=200, body="")
        assert list(cloud.iter_issues("x")) == []

    def test_is_lazy(self, http, cloud):
        http.post(self.URL, json={"issues": issues("A-1"), "nextPageToken": "t1"})
        gen = cloud.iter_issues("x", page_size=1)
        assert len(http.calls) == 0
        assert next(gen) == {"key": "A-1"}
        assert len(http.calls) == 1


class TestSearchIssueWithJql:
    @pytest.mark.parametrize(
        "base, path",
        [(SERVER, "/rest/api/2/search"), (CLOUD, "/rest/api/2/search/jql")],
    )
    def test_max_result_becomes_page_size(self, http, base, path):
        http.post(base + path, json={"issues": issues("A-1"), "total": 1})
        client = Jira(url=base, token="t")
        assert client.search_issue_with_jql("x", max_result=7) == issues("A-1")
        assert sent_json(http.calls[0])["maxResults"] == 7

    def test_default_page_size_is_1000(self, http, server):
        http.post(f"{SERVER}/rest/api/2/search", json={"issues": [], "total": 0})
        server.search_issue_with_jql("x")
        assert sent_json(http.calls[0])["maxResults"] == 1000

    def test_fields_are_passed_through(self, http, cloud):
        http.post(f"{CLOUD}/rest/api/2/search/jql", json={"issues": []})
        cloud.search_issue_with_jql("x", fields=["summary"])
        assert sent_json(http.calls[0])["fields"] == ["summary"]


class TestCountIssues:
    def test_cloud_uses_approximate_count(self, http, cloud):
        http.post(
            f"{CLOUD}/rest/api/2/search/approximate-count",
            match=[matchers.json_params_matcher({"jql": "project = A"})],
            json={"count": 42},
        )
        assert cloud.count_issues("project = A") == 42

    def test_server_reads_total_from_an_empty_search(self, http, server):
        http.post(
            f"{SERVER}/rest/api/2/search",
            match=[
                matchers.json_params_matcher(
                    {"jql": "project = A", "maxResults": 0, "fields": ["id"]}
                )
            ],
            json={"total": 17, "issues": []},
        )
        assert server.count_issues("project = A") == 17

    @pytest.mark.parametrize("response", [{"body": ""}, {"json": {}}])
    def test_empty_responses_count_zero(self, http, jira, response):
        path = "search/approximate-count" if jira.cloud else "search"
        http.post(f"{jira.url}/rest/api/2/{path}", status=200, **response)
        assert jira.count_issues("x") == 0


# ----------------------------------------------------------------------
# Updating issues
# ----------------------------------------------------------------------


class TestUpdateIssue:
    def test_sends_fields_and_update(self, http, jira):
        http.put(f"{jira.url}/rest/api/2/issue/A-1", status=204)
        result = jira.update_issue(
            "A-1", fields={"summary": "New"}, update={"labels": [{"add": "x"}]}
        )
        assert result is None
        assert sent_json(http.calls[0]) == {
            "fields": {"summary": "New"},
            "update": {"labels": [{"add": "x"}]},
        }
        assert http.calls[0].request.params == {}  # notifies users by default

    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            ({"fields": {"summary": "New"}}, {"fields": {"summary": "New"}}),
            ({"update": {}}, {}),  # empty parts are dropped
            ({"fields": {}, "update": {"a": 1}}, {"update": {"a": 1}}),
            ({}, {}),
        ],
    )
    def test_payload_has_only_non_empty_parts(self, http, jira, kwargs, expected):
        http.put(f"{jira.url}/rest/api/2/issue/A-1", status=204)
        jira.update_issue("A-1", **kwargs)
        assert sent_json(http.calls[0]) == expected

    def test_notify_users_false_adds_query_parameter(self, http, jira):
        http.put(
            f"{jira.url}/rest/api/2/issue/A-1",
            match=[matchers.query_param_matcher({"notifyUsers": "false"})],
            status=204,
        )
        jira.update_issue("A-1", fields={"summary": "x"}, notify_users=False)


# ----------------------------------------------------------------------
# Fields and users
# ----------------------------------------------------------------------


FIELDS = [
    {"id": "summary", "name": "Summary", "custom": False},
    {"id": "customfield_10016", "name": "Story Points", "custom": True},
    {"id": "customfield_10020", "name": "Sprint", "custom": True},
    {"id": "customfield_10100", "name": "sprint", "custom": True},
    {"id": "nameless"},
]


class TestFields:
    def test_get_fields(self, http, jira):
        http.get(f"{jira.url}/rest/api/2/field", json=FIELDS)
        fields = jira.get_fields()
        assert [f.id for f in fields][:2] == ["summary", "customfield_10016"]
        assert fields[1].custom is True

    @pytest.mark.parametrize("name", ["Story Points", "story points", "STORY POINTS"])
    def test_get_field_id_ignores_case(self, http, jira, name):
        http.get(f"{jira.url}/rest/api/2/field", json=FIELDS)
        assert jira.get_field_id(name) == "customfield_10016"

    def test_unknown_name_raises(self, http, jira):
        http.get(f"{jira.url}/rest/api/2/field", json=FIELDS)
        with pytest.raises(ValueError, match=r"No field named 'Epic Link': \[\]"):
            jira.get_field_id("Epic Link")

    def test_ambiguous_name_raises_and_lists_candidates(self, http, jira):
        http.get(f"{jira.url}/rest/api/2/field", json=FIELDS)
        with pytest.raises(ValueError, match="2 fields named 'Sprint'") as exc:
            jira.get_field_id("Sprint")
        assert "customfield_10020" in str(exc.value)
        assert "customfield_10100" in str(exc.value)

    @pytest.mark.parametrize(
        "response", [{"body": ""}, {"json": {"errorMessages": ["boom"]}}]
    )
    def test_non_list_response_means_no_match(self, http, jira, response):
        http.get(f"{jira.url}/rest/api/2/field", status=200, **response)
        with pytest.raises(ValueError, match="No field named"):
            jira.get_field_id("Summary")


class TestSearchUsers:
    def test_server_searches_by_username(self, http, server):
        http.get(
            f"{SERVER}/rest/api/2/user/search",
            match=[
                matchers.query_param_matcher({"username": "ada", "maxResults": "50"})
            ],
            json=[{"name": "ada", "displayName": "Ada"}],
        )
        assert server.search_users("ada")[0].name == "ada"

    def test_cloud_searches_by_query(self, http, cloud):
        http.get(
            f"{CLOUD}/rest/api/2/user/search",
            match=[
                matchers.query_param_matcher(
                    {"query": "ada@acme.com", "maxResults": "5"}
                )
            ],
            json=[{"accountId": "abc", "displayName": "Ada"}],
        )
        assert cloud.search_users("ada@acme.com", max_results=5)[0].accountId == "abc"


# ----------------------------------------------------------------------
# Worklogs
# ----------------------------------------------------------------------


class TestWorklogs:
    def test_add_worklog_minimal(self, http, jira):
        http.post(f"{jira.url}/rest/api/2/issue/A-1/worklog", json={"id": "1"})
        assert jira.add_worklog("A-1", "1h 30m") == {"id": "1"}
        assert sent_json(http.calls[0]) == {"timeSpent": "1h 30m"}

    def test_add_worklog_with_comment_and_start(self, http, jira):
        http.post(f"{jira.url}/rest/api/2/issue/A-1/worklog", json={"id": "1"})
        jira.add_worklog(
            "A-1", "2h", comment="pairing", started="2026-10-26T09:00:00.000+0000"
        )
        assert sent_json(http.calls[0]) == {
            "timeSpent": "2h",
            "comment": "pairing",
            "started": "2026-10-26T09:00:00.000+0000",
        }

    def test_empty_comment_is_still_sent(self, http, jira):
        # Only ``None`` means "not given"; an explicit empty string is sent.
        http.post(f"{jira.url}/rest/api/2/issue/A-1/worklog", json={})
        jira.add_worklog("A-1", "1h", comment="")
        assert sent_json(http.calls[0]) == {"timeSpent": "1h", "comment": ""}

    def test_get_worklogs(self, http, jira):
        http.get(
            f"{jira.url}/rest/api/2/issue/A-1/worklog",
            json={"total": 1, "worklogs": [{"id": "1", "timeSpent": "1h"}]},
        )
        assert jira.get_worklogs("A-1").worklogs[0].timeSpent == "1h"


# ----------------------------------------------------------------------
# Attachments
# ----------------------------------------------------------------------


class TestAddAttachment:
    def test_multipart_upload_with_csrf_bypass_header(self, http, jira):
        http.post(
            f"{jira.url}/rest/api/2/issue/A-1/attachments",
            json=[{"id": "10", "filename": "notes.txt"}],
        )
        data = b"hello \x00\xff bytes"
        result = jira.add_attachment("A-1", "notes.txt", data, "text/plain")

        assert result == [{"id": "10", "filename": "notes.txt"}]
        request = http.calls[0].request
        assert request.headers["X-Atlassian-Token"] == "no-check"
        assert request.headers["Content-Type"].startswith("multipart/form-data")
        assert b'name="file"; filename="notes.txt"' in request.body
        assert b"Content-Type: text/plain" in request.body
        assert data in request.body

    def test_header_does_not_leak_into_session(self, http, jira):
        http.post(f"{jira.url}/rest/api/2/issue/A-1/attachments", json=[])
        jira.add_attachment("A-1", "a.bin", b"x")
        assert "X-Atlassian-Token" not in jira._session.headers
        http.get(f"{jira.url}/rest/api/2/issue/A-1", json={})
        jira.issue("A-1")
        assert "X-Atlassian-Token" not in http.calls[1].request.headers

    def test_content_type_defaults_to_octet_stream(self, http, jira):
        http.post(f"{jira.url}/rest/api/2/issue/A-1/attachments", json=[])
        jira.add_attachment("A-1", "a.bin", b"x")
        assert b"Content-Type: application/octet-stream" in http.calls[0].request.body


class TestAttachmentDownload:
    META = f"{SERVER}/rest/api/2/attachment/10"
    CONTENT = f"{SERVER}/secure/attachment/10/notes.txt"

    def test_get_attachment(self, http, server):
        http.get(self.META, json={"id": "10", "content": self.CONTENT})
        assert server.get_attachment("10").content == self.CONTENT

    def test_download_returns_bytes(self, http, server):
        http.get(self.META, json={"id": "10", "content": self.CONTENT})
        http.get(self.CONTENT, body=b"\x00binary\xff", content_type="text/plain")
        assert server.download_attachment("10") == b"\x00binary\xff"
        assert [c.request.url for c in http.calls] == [self.META, self.CONTENT]

    def test_download_streams_to_path(self, http, server, tmp_path):
        http.get(self.META, json={"id": "10", "content": self.CONTENT})
        payload = b"x" * (200 * 1024)  # several 64 KiB chunks
        http.get(self.CONTENT, body=payload)
        target = tmp_path / "notes.txt"
        result = server.download_attachment("10", target)
        assert result == target
        assert target.read_bytes() == payload

    def test_download_accepts_str_path(self, http, cloud, tmp_path):
        meta = f"{CLOUD}/rest/api/2/attachment/10"
        content = f"{CLOUD}/rest/api/3/attachment/content/10"
        http.get(meta, json={"content": content})
        http.get(content, body=b"abc")
        result = cloud.download_attachment("10", str(tmp_path / "a.bin"))
        assert result == tmp_path / "a.bin"
        assert result.read_bytes() == b"abc"

    @pytest.mark.parametrize(
        "meta", [{"json": {"id": "10"}}, {"json": {"content": ""}}, {"body": ""}]
    )
    def test_missing_content_url_raises(self, http, server, meta):
        http.get(self.META, status=200, **meta)
        with pytest.raises(APIError, match="Attachment 10 has no content URL") as exc:
            server.download_attachment("10")
        assert exc.value.code is None
        assert len(http.calls) == 1

    def test_content_url_on_another_host_is_refused(self, http, server):
        http.get(self.META, json={"content": "https://evil.example/steal"})
        with pytest.raises(ValueError, match="another host"):
            server.download_attachment("10")
        assert len(http.calls) == 1  # no request (and no credentials) went out

    def test_download_error_status_raises(self, http, server, tmp_path):
        http.get(self.META, json={"content": self.CONTENT})
        http.get(self.CONTENT, status=404, body="gone")
        with pytest.raises(APIError) as exc:
            server.download_attachment("10", tmp_path / "x")
        assert exc.value.code == 404
        assert not (tmp_path / "x").exists()


class TestDeleteAttachment:
    def test_delete(self, http, jira):
        http.delete(f"{jira.url}/rest/api/2/attachment/10", status=204)
        assert jira.delete_attachment("10") is None
        assert http.calls[0].request.method == "DELETE"

    def test_error_is_raised(self, http, jira):
        http.delete(f"{jira.url}/rest/api/2/attachment/10", status=403, body="no")
        with pytest.raises(APIError) as exc:
            jira.delete_attachment("10")
        assert exc.value.code == 403

"""Jira Software (Agile) boards, sprints and epics.

Requests go through a real ``requests`` session; ``responses`` fakes only the
transport, so paths, query strings and JSON bodies are checked as sent.

Paths, parameters and limits follow the Jira Software Cloud OpenAPI file and
the Jira Software Data Center REST reference. Responses are served strictly
in the order they are registered and each one only once, so a request the
test did not expect (a wrong path, a paging loop that does not stop) fails
with a ``ConnectionError`` instead of hanging, and a request that is never
sent fails the test as well.
"""

import json
from itertools import islice
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

import pytest
import responses
from responses import matchers
from responses.registries import OrderedRegistry

from atlassian_api import Jira
from atlassian_api.error import APIError, NotFoundError

SERVER = "https://jira.company.com"
CLOUD = "https://acme.atlassian.net"
AGILE = "/rest/agile/1.0"
SOFTWARE = "/rest/software/1.0"


@pytest.fixture
def http(monkeypatch):
    """Intercept HTTP at the transport adapter, in strict registration order."""
    for name in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTP_PROXY", "HTTPS_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    with responses.RequestsMock(registry=OrderedRegistry) as rsps:
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


def sent_query(call):
    return dict(parse_qsl(urlsplit(call.request.url).query))


def sent_path(call):
    return urlsplit(call.request.url).path


def query(**params):
    """Match the query string exactly: no parameter more, none less."""
    return [matchers.query_param_matcher({k: str(v) for k, v in params.items()})]


def items(*ids):
    return [{"id": i} for i in ids]


def issues(*keys):
    return [{"key": key} for key in keys]


def keys(result):
    return [issue.key for issue in result]


# ----------------------------------------------------------------------
# Boards, sprints and epics: "values" pages, identical on both deployments
# ----------------------------------------------------------------------


class TestGetBoards:
    def test_filters_and_first_page_parameters(self, http, jira):
        http.get(
            f"{jira.url}{AGILE}/board",
            match=query(
                projectKeyOrId="TEST",
                name="team",
                type="scrum",
                startAt=0,
                maxResults=50,
            ),
            json={
                "isLast": True,
                "values": [{"id": 84, "name": "team board", "type": "scrum"}],
            },
        )
        boards = jira.get_boards(project="TEST", name="team", board_type="scrum")
        assert isinstance(boards[0], SimpleNamespace)
        assert [(b.id, b.name, b.type) for b in boards] == [(84, "team board", "scrum")]

    def test_filters_are_left_out_when_not_given(self, http, jira):
        http.get(
            f"{jira.url}{AGILE}/board",
            match=query(startAt=0, maxResults=50),
            json={"isLast": True, "values": items(1)},
        )
        assert [b.id for b in jira.get_boards()] == [1]

    def test_filter_values_are_url_encoded(self, http, server):
        http.get(f"{SERVER}{AGILE}/board", json={"isLast": True, "values": []})
        server.get_boards(name="R&D #1 board")
        assert "name=R%26D+%231+board" in http.calls[0].request.url
        assert sent_query(http.calls[0])["name"] == "R&D #1 board"

    def test_pages_until_is_last(self, http, jira):
        url = f"{jira.url}{AGILE}/board"
        for start_at, page, is_last in [
            (0, (1, 2), False),
            (2, (3, 4), False),
            (4, (5,), True),
        ]:
            http.get(
                url,
                match=query(startAt=start_at, maxResults=50),
                json={"isLast": is_last, "total": 5, "values": items(*page)},
            )
        assert [b.id for b in jira.get_boards()] == [1, 2, 3, 4, 5]
        assert len(http.calls) == 3

    def test_start_at_advances_by_items_received_not_page_size(self, http, server):
        # Jira may return fewer items than requested.
        url = f"{SERVER}{AGILE}/board"
        http.get(url, json={"isLast": False, "values": items(1)})
        http.get(url, json={"isLast": False, "values": items(2, 3)})
        http.get(url, json={"isLast": True, "values": items(4)})
        assert [b.id for b in server.get_boards()] == [1, 2, 3, 4]
        assert [sent_query(c)["startAt"] for c in http.calls] == ["0", "1", "3"]

    def test_is_last_stops_even_if_total_claims_more(self, http, server):
        http.get(
            f"{SERVER}{AGILE}/board",
            json={"isLast": True, "total": 99, "values": items(1)},
        )
        assert [b.id for b in server.get_boards()] == [1]

    def test_is_last_false_wins_over_a_reached_total(self, http, server):
        url = f"{SERVER}{AGILE}/board"
        http.get(url, json={"isLast": False, "total": 1, "values": items(1)})
        http.get(url, json={"isLast": True, "total": 1, "values": items(2)})
        assert [b.id for b in server.get_boards()] == [1, 2]

    def test_empty_page_stops_even_if_not_last(self, http, server):
        url = f"{SERVER}{AGILE}/board"
        http.get(url, json={"isLast": False, "values": items(1)})
        http.get(url, json={"isLast": False, "values": []})
        assert [b.id for b in server.get_boards()] == [1]
        assert len(http.calls) == 2

    def test_without_is_last_the_total_ends_the_listing(self, http, server):
        url = f"{SERVER}{AGILE}/board"
        http.get(url, json={"total": 3, "values": items(1, 2)})
        http.get(url, json={"total": 3, "values": items(3)})
        assert [b.id for b in server.get_boards()] == [1, 2, 3]
        assert [sent_query(c)["startAt"] for c in http.calls] == ["0", "2"]

    def test_without_is_last_and_total_reads_until_an_empty_page(self, http, server):
        # Data Center documents "total" as optional.
        url = f"{SERVER}{AGILE}/board"
        http.get(url, json={"values": items(1, 2)})
        http.get(url, json={"values": items(3)})
        http.get(url, json={"values": []})
        assert [b.id for b in server.get_boards()] == [1, 2, 3]
        assert [sent_query(c)["startAt"] for c in http.calls] == ["0", "2", "3"]

    @pytest.mark.parametrize(
        "response", [{"body": ""}, {"json": {}}, {"json": None}, {"body": "ok"}]
    )
    def test_response_without_values_is_an_empty_list(self, http, server, response):
        http.get(f"{SERVER}{AGILE}/board", status=200, **response)
        assert server.get_boards() == []

    def test_error_is_raised(self, http, server):
        http.get(f"{SERVER}{AGILE}/board", status=403, body="no license")
        with pytest.raises(APIError) as exc:
            server.get_boards()
        assert exc.value.code == 403


class TestLimit:
    URL = f"{SERVER}{AGILE}/board"

    def test_requests_only_what_is_still_wanted(self, http, server):
        http.get(
            self.URL,
            match=query(startAt=0, maxResults=3),
            json={"isLast": False, "values": items(1, 2)},
        )
        http.get(
            self.URL,
            match=query(startAt=2, maxResults=1),
            json={"isLast": False, "values": items(3)},
        )
        assert [b.id for b in server.get_boards(limit=3)] == [1, 2, 3]
        assert len(http.calls) == 2

    def test_page_size_is_capped_at_50(self, http, server):
        ids = list(range(1, 121))
        for start in (0, 50, 100):
            http.get(
                self.URL, json={"isLast": False, "values": items(*ids[start:][:50])}
            )
        assert [b.id for b in server.get_boards(limit=120)] == ids
        sent = [sent_query(c) for c in http.calls]
        assert [q["maxResults"] for q in sent] == ["50", "50", "20"]
        assert [q["startAt"] for q in sent] == ["0", "50", "100"]

    def test_stops_as_soon_as_the_limit_is_reached(self, http, server):
        http.get(self.URL, json={"isLast": False, "values": items(1, 2)})
        assert [b.id for b in server.get_boards(limit=2)] == [1, 2]
        assert len(http.calls) == 1

    def test_extra_items_from_the_server_are_cut_off(self, http, server):
        http.get(self.URL, json={"isLast": False, "values": items(1, 2, 3, 4, 5)})
        assert [b.id for b in server.get_boards(limit=2)] == [1, 2]

    def test_fewer_items_than_the_limit(self, http, server):
        http.get(self.URL, json={"isLast": True, "values": items(1, 2)})
        assert [b.id for b in server.get_boards(limit=10)] == [1, 2]
        assert sent_query(http.calls[0])["maxResults"] == "10"

    @pytest.mark.parametrize("limit", [0, -1])
    def test_no_request_for_a_limit_below_one(self, http, server, limit):
        assert server.get_boards(limit=limit) == []
        assert len(http.calls) == 0

    def test_applies_to_sprints_and_epics(self, http, server):
        http.get(
            f"{SERVER}{AGILE}/board/84/sprint",
            match=query(startAt=0, maxResults=1),
            json={"isLast": False, "values": items(37)},
        )
        http.get(
            f"{SERVER}{AGILE}/board/84/epic",
            match=query(startAt=0, maxResults=1),
            json={"isLast": False, "values": items(10)},
        )
        assert [s.id for s in server.get_board_sprints(84, limit=1)] == [37]
        assert [e.id for e in server.get_board_epics(84, limit=1)] == [10]


class TestBoardSprintsAndEpics:
    def test_sprints_filtered_by_state(self, http, jira):
        http.get(
            f"{jira.url}{AGILE}/board/84/sprint",
            match=query(state="active,future", startAt=0, maxResults=50),
            json={
                "isLast": True,
                "values": [
                    {"id": 37, "name": "Sprint 1", "state": "active"},
                    {"id": 38, "name": "Sprint 2", "state": "future"},
                ],
            },
        )
        sprints = jira.get_board_sprints(84, state="active,future")
        assert [(s.id, s.state) for s in sprints] == [(37, "active"), (38, "future")]

    def test_sprints_of_every_state_and_all_pages(self, http, jira):
        url = f"{jira.url}{AGILE}/board/84/sprint"
        http.get(
            url,
            match=query(startAt=0, maxResults=50),
            json={"isLast": False, "values": items(1, 2)},
        )
        http.get(
            url,
            match=query(startAt=2, maxResults=50),
            json={"isLast": True, "values": items(3)},
        )
        assert [s.id for s in jira.get_board_sprints(84)] == [1, 2, 3]

    def test_board_without_sprints_raises(self, http, server):
        http.get(
            f"{SERVER}{AGILE}/board/9/sprint",
            status=400,
            json={"errorMessages": ["The board does not support sprints"]},
        )
        with pytest.raises(APIError) as exc:
            server.get_board_sprints(9)
        assert exc.value.code == 400

    @pytest.mark.parametrize("done, sent", [(True, "true"), (False, "false")])
    def test_epics_filtered_by_done(self, http, jira, done, sent):
        http.get(
            f"{jira.url}{AGILE}/board/84/epic",
            match=query(done=sent, startAt=0, maxResults=50),
            json={"isLast": True, "values": [{"id": 10, "name": "E", "done": done}]},
        )
        assert [e.done for e in jira.get_board_epics(84, done=done)] == [done]

    def test_epics_done_or_not_and_all_pages(self, http, jira):
        url = f"{jira.url}{AGILE}/board/84/epic"
        http.get(
            url,
            match=query(startAt=0, maxResults=50),
            json={"isLast": False, "values": items(10)},
        )
        http.get(
            url,
            match=query(startAt=1, maxResults=50),
            json={"isLast": True, "values": items(11)},
        )
        assert [e.id for e in jira.get_board_epics(84)] == [10, 11]


class TestGetOne:
    @pytest.mark.parametrize(
        "method, arg, path",
        [
            ("get_board", 84, "/board/84"),
            ("get_sprint", 37, "/sprint/37"),
            ("get_epic", "TEST-5", "/epic/TEST-5"),
            ("get_epic", 10005, "/epic/10005"),
        ],
    )
    def test_path_and_namespace_result(self, http, jira, method, arg, path):
        http.get(
            f"{jira.url}{AGILE}{path}",
            match=query(),
            json={"id": 1, "name": "N", "location": {"projectKey": "TEST"}},
        )
        result = getattr(jira, method)(arg)
        assert (result.id, result.name, result.location.projectKey) == (1, "N", "TEST")

    def test_missing_sprint_raises_not_found(self, http, server):
        http.get(f"{SERVER}{AGILE}/sprint/404", status=404, body="gone")
        with pytest.raises(NotFoundError):
            server.get_sprint(404)


# ----------------------------------------------------------------------
# Issues of a board, backlog, sprint or epic
# ----------------------------------------------------------------------

ISSUE_LISTS = [
    ("iter_board_issues", 84, "/board/84/issue"),
    ("iter_backlog_issues", 84, "/board/84/backlog"),
    ("iter_sprint_issues", 37, "/sprint/37/issue"),
    ("iter_epic_issues", "TEST-5", "/epic/TEST-5/issue"),
]


class TestIssueListPaths:
    @pytest.mark.parametrize("method, arg, path", ISSUE_LISTS)
    def test_server_pages_the_agile_api_with_start_at(
        self, http, server, method, arg, path
    ):
        url = f"{SERVER}{AGILE}{path}"
        http.get(
            url,
            match=query(maxResults=100, startAt=0),
            json={"total": 3, "issues": issues("A-1", "A-2")},
        )
        http.get(
            url,
            match=query(maxResults=100, startAt=2),
            json={"total": 3, "issues": issues("A-3")},
        )
        assert keys(getattr(server, method)(arg)) == ["A-1", "A-2", "A-3"]

    @pytest.mark.parametrize("method, arg, path", ISSUE_LISTS)
    def test_cloud_pages_the_software_api_with_tokens(
        self, http, cloud, method, arg, path
    ):
        # /rest/agile/1.0/.../issue is deprecated on Cloud.
        url = f"{CLOUD}{SOFTWARE}{path}"
        http.get(
            url,
            match=query(maxResults=100),
            json={"isLast": False, "nextPageToken": "t1", "issues": issues("A-1")},
        )
        http.get(
            url,
            match=query(maxResults=100, nextPageToken="t1"),
            json={"isLast": True, "issues": issues("A-2")},
        )
        assert keys(getattr(cloud, method)(arg)) == ["A-1", "A-2"]

    @pytest.mark.parametrize("method, arg, path", ISSUE_LISTS)
    def test_cloud_flag_selects_the_api_on_a_custom_domain(
        self, http, method, arg, path
    ):
        custom = Jira(url="https://jira.acme.com", token="t", cloud=True)
        http.get(f"https://jira.acme.com{SOFTWARE}{path}", json={"issues": []})
        assert list(getattr(custom, method)(arg)) == []


class TestIterIssuesServer:
    URL = f"{SERVER}{AGILE}/sprint/37/issue"

    def test_pages_until_total_reached(self, http, server):
        for start_at, page in [(0, ("A-1", "A-2")), (2, ("A-3", "A-4")), (4, ("A-5",))]:
            http.get(
                self.URL,
                match=query(maxResults=2, startAt=start_at),
                json={"total": 5, "issues": issues(*page)},
            )
        got = server.iter_sprint_issues(37, page_size=2)
        assert keys(got) == ["A-1", "A-2", "A-3", "A-4", "A-5"]
        assert len(http.calls) == 3

    def test_start_at_advances_by_issues_received_not_page_size(self, http, server):
        # Jira caps the page size (jira.search.views.default.max).
        http.get(self.URL, json={"total": 3, "issues": issues("A-1")})
        http.get(self.URL, json={"total": 3, "issues": issues("A-2", "A-3")})
        assert len(list(server.iter_sprint_issues(37, page_size=5000))) == 3
        assert [sent_query(c)["startAt"] for c in http.calls] == ["0", "1"]
        assert [sent_query(c)["maxResults"] for c in http.calls] == ["5000", "5000"]

    def test_empty_page_stops_even_if_total_claims_more(self, http, server):
        http.get(self.URL, json={"total": 10, "issues": issues("A-1")})
        http.get(self.URL, json={"total": 10, "issues": []})
        # Bounded, so a regression fails instead of looping forever.
        assert len(list(islice(server.iter_sprint_issues(37), 5))) == 1
        assert len(http.calls) == 2

    def test_without_total_reads_until_an_empty_page(self, http, server):
        # Data Center documents "total" as optional.
        http.get(self.URL, json={"issues": issues("A-1", "A-2")})
        http.get(self.URL, json={"issues": issues("A-3")})
        http.get(self.URL, json={"issues": []})
        got = list(islice(server.iter_sprint_issues(37), 10))
        assert keys(got) == ["A-1", "A-2", "A-3"]
        assert [sent_query(c)["startAt"] for c in http.calls] == ["0", "2", "3"]

    def test_total_zero_with_issues_ends_after_the_page(self, http, server):
        http.get(self.URL, json={"total": 0, "issues": issues("A-1")})
        assert len(list(islice(server.iter_sprint_issues(37), 5))) == 1

    def test_jql_and_fields_are_sent_on_every_page(self, http, server):
        for start_at, page in [(0, ("A-1",)), (1, ("A-2",))]:
            http.get(
                self.URL,
                match=query(
                    maxResults=1,
                    startAt=start_at,
                    jql="status != Done ORDER BY created",
                    fields="summary,status",
                ),
                json={"total": 2, "issues": issues(*page)},
            )
        got = server.iter_sprint_issues(
            37,
            jql="status != Done ORDER BY created",
            fields=["summary", "status"],
            page_size=1,
        )
        assert keys(got) == ["A-1", "A-2"]

    def test_jql_and_fields_are_left_out_when_not_given(self, http, server):
        http.get(
            self.URL,
            match=query(maxResults=100, startAt=0),
            json={"total": 1, "issues": issues("A-1")},
        )
        assert keys(server.iter_sprint_issues(37, jql="", fields=None)) == ["A-1"]

    def test_issues_are_namespaces_with_agile_fields(self, http, server):
        issue = {
            "key": "A-1",
            "fields": {
                "summary": "S",
                "status": {"name": "In Progress"},
                "sprint": {"id": 37, "state": "active"},
                "flagged": True,
            },
        }
        http.get(self.URL, json={"total": 1, "issues": [issue]})
        (got,) = server.iter_sprint_issues(37)
        assert isinstance(got, SimpleNamespace)
        assert got.fields.status.name == "In Progress"
        assert (got.fields.sprint.id, got.fields.flagged) == (37, True)

    @pytest.mark.parametrize(
        "response", [{"body": ""}, {"json": {}}, {"json": None}, {"body": "ok"}]
    )
    def test_response_without_issues_yields_nothing(self, http, server, response):
        http.get(self.URL, status=200, **response)
        assert list(server.iter_sprint_issues(37)) == []

    def test_is_lazy(self, http, server):
        http.get(self.URL, json={"total": 4, "issues": issues("A-1", "A-2")})
        gen = server.iter_sprint_issues(37, page_size=2)
        assert len(http.calls) == 0  # nothing is sent until iteration starts
        assert next(gen).key == "A-1"
        assert next(gen).key == "A-2"
        assert len(http.calls) == 1  # the second page is not fetched yet

    def test_error_on_a_later_page_is_raised(self, http, server):
        http.get(self.URL, json={"total": 2, "issues": issues("A-1")})
        http.get(self.URL, status=404, body="sprint deleted")
        gen = server.iter_sprint_issues(37)
        assert next(gen).key == "A-1"
        with pytest.raises(NotFoundError):
            next(gen)


class TestIterIssuesCloud:
    URL = f"{CLOUD}{SOFTWARE}/sprint/37/issue"

    def test_is_last_false_then_true(self, http, cloud):
        http.get(
            self.URL,
            match=query(maxResults=2),
            json={
                "isLast": False,
                "nextPageToken": "t1",
                "issues": issues("A-1", "A-2"),
            },
        )
        http.get(
            self.URL,
            match=query(maxResults=2, nextPageToken="t1"),
            json={
                "isLast": False,
                "nextPageToken": "t2",
                "issues": issues("A-3", "A-4"),
            },
        )
        http.get(
            self.URL,
            match=query(maxResults=2, nextPageToken="t2"),
            json={"isLast": True, "issues": issues("A-5")},
        )
        got = cloud.iter_sprint_issues(37, page_size=2)
        assert keys(got) == ["A-1", "A-2", "A-3", "A-4", "A-5"]
        assert len(http.calls) == 3

    def test_jql_and_fields_are_kept_with_the_token(self, http, cloud):
        common = {"maxResults": 1, "jql": "assignee = 5b10", "fields": "summary,status"}
        http.get(
            self.URL,
            match=query(**common),
            json={"nextPageToken": "t1", "issues": issues("A-1")},
        )
        http.get(
            self.URL,
            match=query(**common, nextPageToken="t1"),
            json={"issues": issues("A-2")},
        )
        got = cloud.iter_sprint_issues(
            37, jql="assignee = 5b10", fields=["summary", "status"], page_size=1
        )
        assert keys(got) == ["A-1", "A-2"]

    def test_never_sends_start_at(self, http, cloud):
        http.get(self.URL, json={"nextPageToken": "t1", "issues": issues("A-1")})
        http.get(self.URL, json={"issues": issues("A-2")})
        list(cloud.iter_sprint_issues(37))
        assert all("startAt" not in sent_query(c) for c in http.calls)

    def test_is_last_wins_over_a_token(self, http, cloud):
        http.get(
            self.URL,
            json={"isLast": True, "nextPageToken": "t1", "issues": issues("A-1")},
        )
        # Bounded, so a regression fails instead of looping forever.
        assert len(list(islice(cloud.iter_sprint_issues(37), 5))) == 1
        assert len(http.calls) == 1

    def test_missing_token_ends_listing(self, http, cloud):
        # The last page carries no nextPageToken.
        http.get(self.URL, json={"isLast": False, "issues": issues("A-1", "A-2")})
        assert len(list(islice(cloud.iter_sprint_issues(37), 5))) == 2
        assert len(http.calls) == 1

    def test_null_token_ends_listing(self, http, cloud):
        http.get(self.URL, json={"nextPageToken": None, "issues": issues("A-1")})
        assert len(list(islice(cloud.iter_sprint_issues(37), 5))) == 1

    def test_empty_page_with_token_ends_listing(self, http, cloud):
        http.get(self.URL, json={"nextPageToken": "t1", "issues": issues("A-1")})
        http.get(self.URL, json={"nextPageToken": "t2", "issues": []})
        assert len(list(islice(cloud.iter_sprint_issues(37), 5))) == 1
        assert len(http.calls) == 2

    def test_total_is_not_needed(self, http, cloud):
        # A "total" would stop Data Center paging here; Cloud has none.
        http.get(
            self.URL,
            json={"total": 1, "nextPageToken": "t1", "issues": issues("A-1")},
        )
        http.get(self.URL, json={"issues": issues("A-2")})
        assert keys(cloud.iter_sprint_issues(37)) == ["A-1", "A-2"]

    @pytest.mark.parametrize("response", [{"body": ""}, {"json": {}}, {"json": None}])
    def test_response_without_issues_yields_nothing(self, http, cloud, response):
        http.get(self.URL, status=200, **response)
        assert list(cloud.iter_sprint_issues(37)) == []

    def test_is_lazy(self, http, cloud):
        http.get(self.URL, json={"nextPageToken": "t1", "issues": issues("A-1")})
        gen = cloud.iter_sprint_issues(37)
        assert len(http.calls) == 0
        assert next(gen).key == "A-1"
        assert len(http.calls) == 1


# ----------------------------------------------------------------------
# Sprints
# ----------------------------------------------------------------------


class TestSprintWrites:
    def test_create_with_required_fields_only(self, http, jira):
        http.post(
            f"{jira.url}{AGILE}/sprint",
            match=[
                matchers.json_params_matcher({"name": "Sprint 12", "originBoardId": 84})
            ],
            status=201,
            json={"id": 40, "state": "future", "name": "Sprint 12"},
        )
        sprint = jira.create_sprint(84, "Sprint 12")
        assert sprint == {"id": 40, "state": "future", "name": "Sprint 12"}

    def test_create_with_dates_and_goal(self, http, jira):
        http.post(
            f"{jira.url}{AGILE}/sprint",
            match=[
                matchers.json_params_matcher(
                    {
                        "name": "Sprint 12",
                        "originBoardId": 84,
                        "startDate": "2026-11-16T09:00:00.000+0000",
                        "endDate": "2026-11-27T17:00:00.000+0000",
                        "goal": "Ship the importer",
                    }
                )
            ],
            status=201,
            json={"id": 40},
        )
        jira.create_sprint(
            84,
            "Sprint 12",
            start_date="2026-11-16T09:00:00.000+0000",
            end_date="2026-11-27T17:00:00.000+0000",
            goal="Ship the importer",
        )

    @pytest.mark.parametrize(
        "kwargs, body",
        [
            ({"state": "active"}, {"state": "active"}),
            ({"name": "Renamed"}, {"name": "Renamed"}),
            ({"goal": ""}, {"goal": ""}),  # an empty goal removes it
            (
                {
                    "name": "N",
                    "state": "closed",
                    "start_date": "2026-11-16T09:00:00.000+0000",
                    "end_date": "2026-11-27T17:00:00.000+0000",
                    "goal": "G",
                },
                {
                    "name": "N",
                    "state": "closed",
                    "startDate": "2026-11-16T09:00:00.000+0000",
                    "endDate": "2026-11-27T17:00:00.000+0000",
                    "goal": "G",
                },
            ),
        ],
    )
    def test_update_is_partial_and_sends_only_given_fields(
        self, http, jira, kwargs, body
    ):
        # POST is the partial update; PUT would reset the fields left out.
        http.post(
            f"{jira.url}{AGILE}/sprint/37",
            match=[matchers.json_params_matcher(body)],
            json={"id": 37, **body},
        )
        assert jira.update_sprint(37, **kwargs) == {"id": 37, **body}

    def test_delete(self, http, jira):
        http.delete(f"{jira.url}{AGILE}/sprint/37", status=204)
        assert jira.delete_sprint(37) is None
        assert http.calls[0].request.method == "DELETE"

    def test_delete_active_sprint_is_refused_by_jira(self, http, server):
        http.delete(f"{SERVER}{AGILE}/sprint/37", status=400, body="sprint is active")
        with pytest.raises(APIError) as exc:
            server.delete_sprint(37)
        assert exc.value.code == 400


# ----------------------------------------------------------------------
# Moving issues: at most 50 per request
# ----------------------------------------------------------------------

MOVES = [
    ("move_issues_to_sprint", (37,), "/sprint/37/issue"),
    ("move_issues_to_backlog", (), "/backlog/issue"),
    ("move_issues_to_epic", ("TEST-5",), "/epic/TEST-5/issue"),
    ("remove_issues_from_epic", (), "/epic/none/issue"),
]


def numbered(count):
    return [f"A-{n}" for n in range(1, count + 1)]


class TestMoveIssues:
    @pytest.mark.parametrize("method, args, path", MOVES)
    def test_path_and_body(self, http, jira, method, args, path):
        http.post(
            f"{jira.url}{AGILE}{path}",
            match=[matchers.json_params_matcher({"issues": ["A-1", "10001", "A-3"]})],
            status=204,
        )
        assert getattr(jira, method)(*args, ["A-1", "10001", "A-3"]) is None

    @pytest.mark.parametrize("method, args, path", MOVES)
    def test_more_than_50_issues_are_sent_in_chunks(
        self, http, server, method, args, path
    ):
        wanted = numbered(120)
        for _ in range(3):
            http.post(f"{SERVER}{AGILE}{path}", status=204)
        getattr(server, method)(*args, wanted)
        chunks = [sent_json(c)["issues"] for c in http.calls]
        assert chunks == [wanted[:50], wanted[50:100], wanted[100:]]

    @pytest.mark.parametrize(
        "count, sizes",
        [
            (1, [1]),
            (49, [49]),
            (50, [50]),
            (51, [50, 1]),
            (99, [50, 49]),
            (100, [50, 50]),
            (101, [50, 50, 1]),
        ],
    )
    def test_chunk_boundaries(self, http, server, count, sizes):
        wanted = numbered(count)
        for _ in sizes:
            http.post(f"{SERVER}{AGILE}/sprint/37/issue", status=204)
        server.move_issues_to_sprint(37, wanted)
        chunks = [sent_json(c)["issues"] for c in http.calls]
        assert [len(chunk) for chunk in chunks] == sizes
        # Every issue is sent exactly once, in the order given.
        assert [key for chunk in chunks for key in chunk] == wanted

    @pytest.mark.parametrize("nothing", [[], (), iter([])])
    def test_no_issues_sends_no_request(self, http, server, nothing):
        assert server.move_issues_to_sprint(37, nothing) is None
        assert len(http.calls) == 0

    def test_a_single_key_can_be_a_string(self, http, server):
        http.post(
            f"{SERVER}{AGILE}/sprint/37/issue",
            match=[matchers.json_params_matcher({"issues": ["TEST-12"]})],
            status=204,
        )
        server.move_issues_to_sprint(37, "TEST-12")

    def test_ids_are_sent_as_strings_and_duplicates_once(self, http, server):
        http.post(
            f"{SERVER}{AGILE}/backlog/issue",
            match=[matchers.json_params_matcher({"issues": ["A-2", "10001", "A-1"]})],
            status=204,
        )
        server.move_issues_to_backlog(["A-2", 10001, "A-1", "A-2", "10001"])

    def test_duplicates_do_not_count_towards_a_chunk(self, http, server):
        http.post(f"{SERVER}{AGILE}/backlog/issue", status=204)
        server.move_issues_to_backlog(numbered(50) + numbered(50))
        assert sent_json(http.calls[0])["issues"] == numbered(50)

    def test_accepts_a_generator(self, http, server):
        http.post(f"{SERVER}{AGILE}/epic/none/issue", status=204)
        server.remove_issues_from_epic(f"A-{n}" for n in (1, 2))
        assert sent_json(http.calls[0])["issues"] == ["A-1", "A-2"]

    def test_failing_chunk_raises_and_stops(self, http, server):
        url = f"{SERVER}{AGILE}/sprint/37/issue"
        http.post(url, status=204)
        http.post(url, status=400, body="Issue A-60 does not exist")
        with pytest.raises(APIError) as exc:
            server.move_issues_to_sprint(37, numbered(120))
        assert exc.value.code == 400
        assert len(http.calls) == 2  # the third chunk is never sent


# ----------------------------------------------------------------------
# End to end: board -> active sprint -> issues
# ----------------------------------------------------------------------


class TestSprintReport:
    @staticmethod
    def report(jira):
        (board,) = jira.get_boards(project="TEST", board_type="scrum")
        (sprint,) = jira.get_board_sprints(board.id, state="active")
        by_status: dict = {}
        for issue in jira.iter_sprint_issues(sprint.id, fields=["status"]):
            by_status.setdefault(issue.fields.status.name, []).append(issue.key)
        return sprint.name, by_status

    @staticmethod
    def issue(key, status):
        return {"key": key, "fields": {"status": {"name": status}}}

    def register_board_and_sprint(self, http, base):
        http.get(
            f"{base}{AGILE}/board",
            match=query(projectKeyOrId="TEST", type="scrum", startAt=0, maxResults=50),
            json={"isLast": True, "values": [{"id": 84, "name": "TEST board"}]},
        )
        http.get(
            f"{base}{AGILE}/board/84/sprint",
            match=query(state="active", startAt=0, maxResults=50),
            json={"isLast": True, "values": [{"id": 37, "name": "Sprint 12"}]},
        )

    def test_on_data_center(self, http, server):
        self.register_board_and_sprint(http, SERVER)
        url = f"{SERVER}{AGILE}/sprint/37/issue"
        http.get(
            url,
            match=query(maxResults=100, fields="status", startAt=0),
            json={
                "total": 3,
                "issues": [self.issue("T-1", "Done"), self.issue("T-2", "To Do")],
            },
        )
        http.get(
            url,
            match=query(maxResults=100, fields="status", startAt=2),
            json={"total": 3, "issues": [self.issue("T-3", "Done")]},
        )
        assert self.report(server) == (
            "Sprint 12",
            {"Done": ["T-1", "T-3"], "To Do": ["T-2"]},
        )

    def test_on_cloud(self, http, cloud):
        self.register_board_and_sprint(http, CLOUD)
        url = f"{CLOUD}{SOFTWARE}/sprint/37/issue"
        http.get(
            url,
            match=query(maxResults=100, fields="status"),
            json={
                "nextPageToken": "t1",
                "issues": [self.issue("T-1", "Done"), self.issue("T-2", "To Do")],
            },
        )
        http.get(
            url,
            match=query(maxResults=100, fields="status", nextPageToken="t1"),
            json={"isLast": True, "issues": [self.issue("T-3", "Done")]},
        )
        assert self.report(cloud) == (
            "Sprint 12",
            {"Done": ["T-1", "T-3"], "To Do": ["T-2"]},
        )
        assert [sent_path(c) for c in http.calls] == [
            f"{AGILE}/board",
            f"{AGILE}/board/84/sprint",
            f"{SOFTWARE}/sprint/37/issue",
            f"{SOFTWARE}/sprint/37/issue",
        ]

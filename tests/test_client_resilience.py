"""Typed errors, retries, HTML-page guard, URL safety and downloads.

Requests go through a real ``requests`` session with the transport mocked by
``responses``. ``no_retry_sleep`` (see ``conftest.py``) records the waits that
the client would have slept.
"""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import MagicMock

import pytest
import responses

from atlassian_api.client import AtlassianAPI
from atlassian_api.error import (
    APIError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    error_for_status,
)

BASE = "https://jira.example.com"
URL = f"{BASE}/rest/api/2/thing"
LOGIN_PAGE = "<html><body>Please log in</body></html>"

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


@pytest.fixture
def client():
    with AtlassianAPI(BASE) as api:
        yield api


def http_date(seconds_from_now):
    moment = datetime.now(timezone.utc) + timedelta(seconds=seconds_from_now)
    return format_datetime(moment, usegmt=True)


def slept(sleep):
    return [call.args[0] for call in sleep.call_args_list]


# ----------------------------------------------------------------------
# error_for_status
# ----------------------------------------------------------------------


class TestErrorForStatus:
    @pytest.mark.parametrize(
        "code, expected",
        [
            (401, AuthenticationError),
            (403, PermissionDeniedError),
            (404, NotFoundError),
            (409, ConflictError),
            (429, RateLimitError),
            (500, ServerError),
            (503, ServerError),
            (599, ServerError),
            (400, APIError),
            (418, APIError),
        ],
    )
    def test_maps_status_to_most_specific_class(self, code, expected):
        error = error_for_status(code, "boom")
        assert type(error) is expected
        assert isinstance(error, APIError)
        assert error.code == code
        assert error.message == "boom"

    def test_falls_back_to_the_standard_message(self):
        assert error_for_status(404).message == "Not Found"
        assert error_for_status(418).message == "Unknown Error"

    def test_rate_limit_carries_retry_after(self):
        error = error_for_status(429, "slow down", retry_after=12.5)
        assert isinstance(error, RateLimitError)
        assert error.retry_after == 12.5

    def test_rate_limit_defaults(self):
        error = RateLimitError()
        assert error.code == 429
        assert error.message == "Unknown Error"  # 429 has no standard text
        assert error.retry_after is None

    def test_other_errors_are_caught_as_api_error(self):
        with pytest.raises(APIError):
            raise error_for_status(404)

    def test_unknown_code_none_uses_generic_message(self):
        assert APIError().message == "Unknown Error"
        assert str(APIError(500)) == "Error [500] : Internal Server Error"


# ----------------------------------------------------------------------
# request(): typed errors
# ----------------------------------------------------------------------


class TestTypedErrors:
    @pytest.mark.parametrize(
        "status, expected",
        [
            (401, AuthenticationError),
            (403, PermissionDeniedError),
            (404, NotFoundError),
            (409, ConflictError),
            (400, APIError),
            (500, ServerError),
        ],
    )
    def test_request_raises_specific_subclass(self, http, client, status, expected):
        http.get(URL, status=status, body="nope")
        with pytest.raises(APIError) as exc:
            client.get("/rest/api/2/thing")
        assert type(exc.value) is expected
        assert exc.value.code == status
        assert exc.value.message == "nope"

    def test_non_cloud_bearer_401_has_no_cloud_hint(self, http):
        http.get(URL, status=401, body="Unauthorized")
        with pytest.raises(AuthenticationError) as exc:
            AtlassianAPI(BASE, token="t").get("/rest/api/2/thing")
        assert exc.value.message == "Unauthorized"


# ----------------------------------------------------------------------
# Retries
# ----------------------------------------------------------------------


class TestRetries:
    def test_success_after_one_429(self, http, client, no_retry_sleep):
        http.get(URL, status=429)
        http.get(URL, json={"ok": True})
        assert client.get("/rest/api/2/thing").ok is True
        assert len(http.calls) == 2
        assert slept(no_retry_sleep) == [1.0]

    def test_429_is_retried_for_post(self, http, client, no_retry_sleep):
        http.post(URL, status=429)
        http.post(URL, json={"id": 1})
        assert client.post("/rest/api/2/thing", json={"a": 1}) == {"id": 1}
        assert len(http.calls) == 2

    def test_503_is_retried_for_get(self, http, client, no_retry_sleep):
        http.get(URL, status=503)
        http.get(URL, json={"ok": True})
        assert client.get("/rest/api/2/thing").ok is True
        assert slept(no_retry_sleep) == [1.0]

    def test_503_is_not_retried_for_post(self, http, client, no_retry_sleep):
        http.post(URL, status=503, body="down")
        with pytest.raises(ServerError):
            client.post("/rest/api/2/thing", json={})
        assert len(http.calls) == 1
        no_retry_sleep.assert_not_called()

    def test_other_server_errors_are_not_retried(self, http, client, no_retry_sleep):
        http.get(URL, status=500)
        with pytest.raises(ServerError):
            client.get("/rest/api/2/thing")
        assert len(http.calls) == 1
        no_retry_sleep.assert_not_called()

    def test_exponential_backoff_without_retry_after(
        self, http, client, no_retry_sleep
    ):
        http.get(URL, status=429, body="slow")
        with pytest.raises(RateLimitError) as exc:
            client.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [1.0, 2.0, 4.0]
        assert len(http.calls) == 4  # max_retries + 1
        assert exc.value.retry_after is None

    def test_backoff_is_capped_by_max_retry_wait(self, http, no_retry_sleep):
        http.get(URL, status=429)
        api = AtlassianAPI(BASE, max_retries=4, max_retry_wait=3)
        with pytest.raises(RateLimitError):
            api.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [1.0, 2.0, 3.0, 3.0]

    def test_max_retries_caps_attempts(self, http, no_retry_sleep):
        http.get(URL, status=503)
        api = AtlassianAPI(BASE, max_retries=1)
        with pytest.raises(ServerError):
            api.get("/rest/api/2/thing")
        assert len(http.calls) == 2
        assert slept(no_retry_sleep) == [1.0]

    def test_max_retries_zero_disables_retrying(self, http, no_retry_sleep):
        http.get(URL, status=429)
        with pytest.raises(RateLimitError):
            AtlassianAPI(BASE, max_retries=0).get("/rest/api/2/thing")
        assert len(http.calls) == 1
        no_retry_sleep.assert_not_called()


class TestRetryAfter:
    def test_seconds_are_honoured(self, http, client, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": "7"})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [7.0]

    def test_negative_seconds_mean_no_wait(self, http, client, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": "-5"})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [0.0]

    def test_future_http_date_is_honoured(self, http, client, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": http_date(30)})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        (delay,) = slept(no_retry_sleep)
        assert 20 < delay <= 30

    def test_http_date_without_timezone_is_read_as_utc(
        self, http, client, no_retry_sleep
    ):
        # "-0000" means "UTC, local zone unknown": parsed as a naive datetime.
        when = datetime.now(timezone.utc) + timedelta(seconds=30)
        header = when.strftime("%a, %d %b %Y %H:%M:%S -0000")
        http.get(URL, status=429, headers={"Retry-After": header})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        (delay,) = slept(no_retry_sleep)
        assert 20 < delay <= 30

    def test_past_http_date_means_no_wait(self, http, client, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": http_date(-3600)})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [0.0]

    @pytest.mark.parametrize("value", ["soon", "", "Tue, 99 Foo 2099 99:99:99 GMT"])
    def test_unusable_value_falls_back_to_backoff(
        self, http, client, no_retry_sleep, value
    ):
        http.get(URL, status=429, headers={"Retry-After": value})
        http.get(URL, status=429, headers={"Retry-After": value})
        http.get(URL, json={"ok": True})
        client.get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [1.0, 2.0]

    def test_longer_than_max_retry_wait_raises_immediately(
        self, http, client, no_retry_sleep
    ):
        http.get(URL, status=429, headers={"Retry-After": "120"})
        with pytest.raises(RateLimitError) as exc:
            client.get("/rest/api/2/thing")
        assert exc.value.retry_after == 120.0
        assert len(http.calls) == 1
        no_retry_sleep.assert_not_called()

    def test_equal_to_max_retry_wait_is_still_honoured(self, http, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": "10"})
        http.get(URL, json={"ok": True})
        AtlassianAPI(BASE, max_retry_wait=10).get("/rest/api/2/thing")
        assert slept(no_retry_sleep) == [10.0]

    def test_final_error_keeps_retry_after(self, http, no_retry_sleep):
        http.get(URL, status=429, headers={"Retry-After": "2"})
        with pytest.raises(RateLimitError) as exc:
            AtlassianAPI(BASE, max_retries=2).get("/rest/api/2/thing")
        assert exc.value.retry_after == 2.0
        assert slept(no_retry_sleep) == [2.0, 2.0]
        assert len(http.calls) == 3


# ----------------------------------------------------------------------
# HTML guard
# ----------------------------------------------------------------------


class TestHtmlGuard:
    def test_get_rejects_html_page(self, http, client):
        http.get(URL, body=LOGIN_PAGE, content_type="text/html; charset=utf-8")
        with pytest.raises(APIError) as exc:
            client.get("/rest/api/2/thing")
        assert exc.value.code == 200
        assert "HTML page" in exc.value.message
        assert "login or SSO" in exc.value.message
        assert URL in exc.value.message

    def test_get_returns_plain_text_as_str(self, http, client):
        http.get(URL, body="pong", content_type="text/plain")
        assert client.get("/rest/api/2/thing") == "pong"

    def test_get_parses_json_even_if_labelled_html(self, http, client):
        http.get(URL, body='{"a": 1}', content_type="text/html")
        assert client.get("/rest/api/2/thing").a == 1

    def test_get_empty_body_is_none(self, http, client):
        http.get(URL, body="", content_type="text/html")
        assert client.get("/rest/api/2/thing") is None

    def test_post_rejects_html_page(self, http, client):
        http.post(URL, body=LOGIN_PAGE, content_type="text/html")
        with pytest.raises(APIError, match="HTML page"):
            client.post("/rest/api/2/thing", json={})

    @pytest.mark.parametrize("content_type", ["text/html", "text/plain"])
    def test_post_empty_body_is_none(self, http, client, content_type):
        http.post(URL, body="", status=204, content_type=content_type)
        assert client.post("/rest/api/2/thing", json={}) is None

    def test_post_non_json_text_is_none(self, http, client):
        http.post(URL, body="created", content_type="text/plain")
        assert client.post("/rest/api/2/thing", json={}) is None

    def test_put_and_delete_share_the_guard(self, http, client):
        http.put(URL, body=LOGIN_PAGE, content_type="text/html")
        http.delete(URL, body='{"gone": true}')
        with pytest.raises(APIError, match="HTML page"):
            client.put("/rest/api/2/thing", json={})
        assert client.delete("/rest/api/2/thing") == {"gone": True}

    def test_unexpected_decoding_failure_returns_none(self):
        response = MagicMock()
        response.json.side_effect = RuntimeError("broken decoder")
        assert AtlassianAPI._response_handler(response) is None


# ----------------------------------------------------------------------
# _resolve_url
# ----------------------------------------------------------------------


class TestResolveUrl:
    def test_relative_path_is_appended_to_base_url(self):
        api = AtlassianAPI(BASE + "/")
        assert api._resolve_url("/rest/api/2/x") == f"{BASE}/rest/api/2/x"

    @pytest.mark.parametrize(
        "url",
        [
            f"{BASE}/secure/attachment/1/a.txt",
            "https://JIRA.Example.COM/secure/attachment/1/a.txt",
            "https://jira.example.com/a?x=1",
        ],
    )
    def test_same_host_absolute_url_is_used_as_is(self, url):
        assert AtlassianAPI(BASE)._resolve_url(url) == url

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example.org/steal",
            "https://jira.example.com.evil.org/steal",
            "http://jira.example.com/a",
            "https://jira.example.com:8443/a",
        ],
    )
    def test_other_host_or_scheme_is_refused(self, http, url):
        api = AtlassianAPI(BASE, username="u", password="p")
        with pytest.raises(ValueError, match="another host"):
            api.get(url)
        assert len(http.calls) == 0  # nothing was sent, so no credentials leaked

    def test_same_host_absolute_url_is_requested(self, http, client):
        target = f"{BASE}/rest/api/2/other"
        http.get(target, json={"ok": True})
        assert client.get(target).ok is True


# ----------------------------------------------------------------------
# _download
# ----------------------------------------------------------------------


class TestDownload:
    def test_returns_bytes_without_path(self, http, client):
        http.get(f"{BASE}/file", body=b"\x00\x01binary")
        assert client._download("/file") == b"\x00\x01binary"

    def test_streams_to_file_and_returns_path(self, http, client, tmp_path):
        payload = b"x" * (200 * 1024)  # several 64 KiB chunks
        http.get(f"{BASE}/file", body=payload)
        target = tmp_path / "out.bin"
        result = client._download("/file", path=str(target))
        assert result == target
        assert target.read_bytes() == payload

    def test_accepts_pathlib_path(self, http, client, tmp_path):
        http.get(f"{BASE}/file", body=b"data")
        result = client._download("/file", path=tmp_path / "out.bin")
        assert result.read_bytes() == b"data"

    def test_passes_query_params(self, http, client):
        http.get(f"{BASE}/file", body=b"d")
        client._download("/file", params={"version": "2"})
        assert http.calls[0].request.url.endswith("/file?version=2")

    def test_reject_html_raises(self, http, client, tmp_path):
        http.get(f"{BASE}/file", body=LOGIN_PAGE, content_type="text/html")
        target = tmp_path / "out.bin"
        with pytest.raises(APIError, match="received an HTML page"):
            client._download("/file", path=target, reject_html=True)
        assert not target.exists()

    def test_reject_html_lets_binary_through(self, http, client):
        http.get(f"{BASE}/file", body=b"PK", content_type="application/zip")
        assert client._download("/file", reject_html=True) == b"PK"

    def test_html_is_saved_when_not_rejected(self, http, client, tmp_path):
        http.get(f"{BASE}/page", body=LOGIN_PAGE, content_type="text/html")
        target = tmp_path / "page.html"
        client._download("/page", path=target)
        assert target.read_text() == LOGIN_PAGE

    def test_http_errors_are_typed(self, http, client):
        http.get(f"{BASE}/file", status=404)
        with pytest.raises(NotFoundError):
            client._download("/file")


# ----------------------------------------------------------------------
# request() pass-through
# ----------------------------------------------------------------------


class TestRequestPassThrough:
    def test_headers_are_sent_for_this_request_only(self, http, client):
        http.post(URL, json={})
        http.get(URL, json={})
        client.request(
            "POST", "/rest/api/2/thing", headers={"X-Atlassian-Token": "no-check"}
        )
        client.request("GET", "/rest/api/2/thing")
        assert http.calls[0].request.headers["X-Atlassian-Token"] == "no-check"
        assert "X-Atlassian-Token" not in http.calls[1].request.headers

    def test_files_are_sent_as_multipart(self, http, client):
        http.post(URL, json={})
        client.request(
            "POST",
            "/rest/api/2/thing",
            files={"file": ("report.txt", b"hello world")},
        )
        request = http.calls[0].request
        assert request.headers["Content-Type"].startswith("multipart/form-data")
        assert b'filename="report.txt"' in request.body
        assert b"hello world" in request.body

    def test_files_are_resent_when_retrying(self, http, client):
        http.post(URL, status=429)
        http.post(URL, json={})
        client.request(
            "POST", "/rest/api/2/thing", files={"file": ("a.txt", b"payload")}
        )
        assert len(http.calls) == 2
        assert all(b"payload" in call.request.body for call in http.calls)

    def test_stream_flag_reaches_the_session(self, http, client):
        http.get(URL, body="x")
        streamed = client.request("GET", "/rest/api/2/thing", stream=True)
        assert http.calls[0].request.req_kwargs["stream"] is True
        assert streamed.content == b"x"

    def test_stream_defaults_to_false(self):
        session = MagicMock()
        session.request.return_value = MagicMock(status_code=200)
        AtlassianAPI(BASE, session=session).request("GET", "/x")
        assert session.request.call_args.kwargs["stream"] is False
        AtlassianAPI(BASE, session=session).request("GET", "/x", stream=True)
        assert session.request.call_args.kwargs["stream"] is True

import base64
import logging

import pytest
from unittest.mock import MagicMock, patch, Mock
import requests
import responses
from responses import matchers
from types import SimpleNamespace
from atlassian.client import AtlassianAPI
from atlassian.error import APIError


class TestAtlassianAPI:
    def test_init_basic(self):
        api = AtlassianAPI(url="https://example.com")
        assert api.url == "https://example.com"
        assert api.username is None
        assert api.password is None
        assert api.timeout == 60
        assert isinstance(api._session, requests.Session)

    def test_init_with_trailing_slash(self):
        api = AtlassianAPI(url="https://example.com/")
        assert api.url == "https://example.com"

    def test_init_with_basic_auth(self):
        api = AtlassianAPI(url="https://example.com", username="user", password="pass")
        assert api.username == "user"
        assert api.password == "pass"
        assert api._session.auth == ("user", "pass")

    def test_init_with_token(self):
        api = AtlassianAPI(url="https://example.com", token="test_token")
        assert "Authorization" in api._session.headers
        assert api._session.headers["Authorization"] == "Bearer test_token"

    def test_init_with_custom_session(self):
        custom_session = requests.Session()
        api = AtlassianAPI(url="https://example.com", session=custom_session)
        assert api._session is custom_session

    def test_init_with_timeout(self):
        api = AtlassianAPI(url="https://example.com", timeout=30)
        assert api.timeout == 30

    def test_init_with_verify_false(self):
        api = AtlassianAPI(url="https://example.com", verify=False)
        assert api._session.verify is False

    def test_init_with_verify_ca_bundle(self):
        api = AtlassianAPI(url="https://example.com", verify="/path/to/ca-bundle.crt")
        assert api._session.verify == "/path/to/ca-bundle.crt"

    def test_init_verify_default_is_true(self):
        api = AtlassianAPI(url="https://example.com")
        assert api._session.verify is True

    def test_init_with_proxies(self):
        proxies = {"https": "http://proxy.example.com:8080"}
        api = AtlassianAPI(url="https://example.com", proxies=proxies)
        assert api._session.proxies.get("https") == "http://proxy.example.com:8080"

    def test_init_without_proxies(self):
        api = AtlassianAPI(url="https://example.com")
        # No custom proxy should be set
        assert api._session.proxies.get("https") is None

    def test_init_with_auth_exception(self):
        with patch.object(
            AtlassianAPI, "_create_basic_session", side_effect=Exception("Auth error")
        ):
            api = AtlassianAPI(
                url="https://example.com", username="user", password="pass"
            )
            assert api.username == "user"

    def test_context_manager_enter(self):
        api = AtlassianAPI(url="https://example.com")
        with api as context_api:
            assert context_api is api

    def test_context_manager_exit(self):
        api = AtlassianAPI(url="https://example.com")
        api._session.close = MagicMock()
        with api:
            pass
        api._session.close.assert_called_once()

    def test_create_basic_session(self):
        api = AtlassianAPI(url="https://example.com")
        api._create_basic_session("testuser", "testpass")
        assert api._session.auth == ("testuser", "testpass")

    def test_create_token_session(self):
        api = AtlassianAPI(url="https://example.com")
        api._create_token_session("my_token")
        assert api._session.headers["Authorization"] == "Bearer my_token"

    def test_update_header(self):
        api = AtlassianAPI(url="https://example.com")
        api._update_header("Custom-Header", "custom-value")
        assert api._session.headers["Custom-Header"] == "custom-value"

    def test_response_handler_with_json(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        result = AtlassianAPI._response_handler(mock_response)
        assert result == {"key": "value"}

    def test_response_handler_with_value_error(self):
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("No JSON")
        result = AtlassianAPI._response_handler(mock_response)
        assert result is None

    def test_response_handler_with_exception(self):
        mock_response = MagicMock()
        mock_response.json.side_effect = Exception("Generic error")
        result = AtlassianAPI._response_handler(mock_response)
        assert result is None

    def test_close(self):
        api = AtlassianAPI(url="https://example.com")
        api._session.close = MagicMock()
        api.close()
        api._session.close.assert_called_once()

    def test_request_with_path(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        api._session.request = MagicMock(return_value=mock_response)

        result = api.request(method="GET", path="/api/test")

        api._session.request.assert_called_once_with(
            method="GET",
            url="https://example.com/api/test",
            data=None,
            json=None,
            params=None,
            timeout=60,
        )
        assert result.encoding == "utf-8"

    def test_request_without_path(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        api._session.request = MagicMock(return_value=mock_response)

        result = api.request(method="GET")

        api._session.request.assert_called_once_with(
            method="GET",
            url="https://example.com",
            data=None,
            json=None,
            params=None,
            timeout=60,
        )

    def test_request_with_all_params(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        api._session.request = MagicMock(return_value=mock_response)

        api.request(
            method="POST",
            path="/api/test",
            data={"key": "value"},
            json={"json_key": "json_value"},
            params={"param": "value"},
        )

        api._session.request.assert_called_once_with(
            method="POST",
            url="https://example.com/api/test",
            data={"key": "value"},
            json={"json_key": "json_value"},
            params={"param": "value"},
            timeout=60,
        )

    def test_get_with_response(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.text = '{"name": "test"}'
        api.request = MagicMock(return_value=mock_response)

        result = api.get("/api/test")

        api.request.assert_called_once_with("GET", "/api/test", data=None, params=None)
        assert isinstance(result, SimpleNamespace)
        assert result.name == "test"

    def test_get_with_empty_response(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.text = ""
        api.request = MagicMock(return_value=mock_response)

        result = api.get("/api/test")

        assert result is None

    def test_get_with_json_error(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.text = "not json"
        api.request = MagicMock(return_value=mock_response)

        result = api.get("/api/test")

        assert result == "not json"

    def test_get_with_params(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.text = '{"result": "ok"}'
        api.request = MagicMock(return_value=mock_response)

        api.get("/api/test", params={"key": "value"})

        api.request.assert_called_once_with(
            "GET", "/api/test", data=None, params={"key": "value"}
        )

    def test_post(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = {"created": True}
        api.request = MagicMock(return_value=mock_response)

        result = api.post("/api/create", json={"name": "test"})

        api.request.assert_called_once_with(
            "POST", "/api/create", data=None, json={"name": "test"}, params=None
        )
        assert result == {"created": True}

    def test_post_with_data(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        api.request = MagicMock(return_value=mock_response)

        api.post("/api/create", data={"key": "value"})

        api.request.assert_called_once_with(
            "POST", "/api/create", data={"key": "value"}, json=None, params=None
        )

    def test_put(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = {"updated": True}
        api.request = MagicMock(return_value=mock_response)

        result = api.put("/api/update", json={"name": "updated"})

        api.request.assert_called_once_with(
            "PUT", "/api/update", data=None, json={"name": "updated"}, params=None
        )
        assert result == {"updated": True}

    def test_put_with_data(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = None
        api.request = MagicMock(return_value=mock_response)

        api.put("/api/update", data={"key": "value"})

        api.request.assert_called_once_with(
            "PUT", "/api/update", data={"key": "value"}, json=None, params=None
        )

    def test_delete(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = {"deleted": True}
        api.request = MagicMock(return_value=mock_response)

        result = api.delete("/api/delete")

        api.request.assert_called_once_with(
            "DELETE", "/api/delete", data=None, json=None, params=None
        )
        assert result == {"deleted": True}

    def test_delete_with_json(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.json.return_value = None
        api.request = MagicMock(return_value=mock_response)

        api.delete("/api/delete", json={"id": 123})

        api.request.assert_called_once_with(
            "DELETE", "/api/delete", data=None, json={"id": 123}, params=None
        )

    def test_request_raises_api_error_on_4xx(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Not Found"
        api._session.request = MagicMock(return_value=mock_response)

        with pytest.raises(APIError) as exc_info:
            api.request(method="GET", path="/api/missing")

        assert exc_info.value.code == 404

    def test_request_raises_api_error_on_401(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.text = "Unauthorized"
        api._session.request = MagicMock(return_value=mock_response)

        with pytest.raises(APIError) as exc_info:
            api.request(method="GET", path="/api/secure")

        assert exc_info.value.code == 401

    def test_request_raises_api_error_on_5xx(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"
        api._session.request = MagicMock(return_value=mock_response)

        with pytest.raises(APIError) as exc_info:
            api.request(method="POST", path="/api/create")

        assert exc_info.value.code == 500

    def test_request_does_not_raise_on_2xx(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.reason = "Created"
        api._session.request = MagicMock(return_value=mock_response)

        result = api.request(method="POST", path="/api/create")

        assert result.status_code == 201

    def test_request_does_not_raise_on_204(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.reason = "No Content"
        api._session.request = MagicMock(return_value=mock_response)

        result = api.request(method="DELETE", path="/api/resource")

        assert result.status_code == 204

    def test_api_error_message_from_response(self):
        api = AtlassianAPI(url="https://example.com")
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = '{"message": "You do not have permission"}'
        api._session.request = MagicMock(return_value=mock_response)

        with pytest.raises(APIError) as exc_info:
            api.request(method="GET", path="/api/admin")

        assert exc_info.value.code == 403
        assert '{"message": "You do not have permission"}' in exc_info.value.message


BASE_URL = "https://jira.example.com"


# requests lets these variables override session settings, so clear them.
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


class TestAtlassianAPIOverHTTP:
    """Exercise the client through a real ``requests`` session."""

    def test_get_decodes_json_into_namespaces(self, http):
        http.get(
            f"{BASE_URL}/rest/api/2/issue/TEST-1",
            json={"key": "TEST-1", "fields": {"status": {"name": "Open"}}},
        )
        api = AtlassianAPI(url=f"{BASE_URL}/")

        issue = api.get("/rest/api/2/issue/TEST-1")

        assert issue.key == "TEST-1"
        assert issue.fields.status.name == "Open"

    def test_secure_transport_defaults(self, http):
        http.get(f"{BASE_URL}/rest/api/2/myself", json={})
        AtlassianAPI(url=BASE_URL).get("/rest/api/2/myself")

        sent = http.calls[0].request
        assert sent.req_kwargs["verify"] is True
        assert sent.req_kwargs["timeout"] == 60
        assert "Authorization" not in sent.headers

    @pytest.mark.parametrize(
        "kwargs, expected",
        [
            ({"verify": False}, {"verify": False}),
            ({"verify": "/etc/ssl/ca.pem"}, {"verify": "/etc/ssl/ca.pem"}),
            ({"timeout": 5}, {"timeout": 5}),
            (
                {"proxies": {"https": "http://proxy.example.com:8080"}},
                {"proxies": {"https": "http://proxy.example.com:8080"}},
            ),
        ],
    )
    def test_transport_options_are_forwarded(self, http, kwargs, expected):
        http.get(f"{BASE_URL}/rest/api/2/myself", json={})
        AtlassianAPI(url=BASE_URL, **kwargs).get("/rest/api/2/myself")

        sent = http.calls[0].request.req_kwargs
        for key, value in expected.items():
            if key == "proxies":
                assert dict(sent[key]).items() >= value.items()
            else:
                assert sent[key] == value

    def test_token_authentication_header(self, http):
        http.get(f"{BASE_URL}/rest/api/2/myself", json={})
        AtlassianAPI(url=BASE_URL, token="tok3n").get("/rest/api/2/myself")

        assert http.calls[0].request.headers["Authorization"] == "Bearer tok3n"

    def test_basic_authentication_header(self, http):
        http.get(f"{BASE_URL}/rest/api/2/myself", json={})
        AtlassianAPI(url=BASE_URL, username="alice", password="s3cr3t").get(
            "/rest/api/2/myself"
        )

        expected = "Basic " + base64.b64encode(b"alice:s3cr3t").decode()
        assert http.calls[0].request.headers["Authorization"] == expected

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 500, 503])
    def test_error_status_raises_api_error_with_body(self, http, status):
        http.get(f"{BASE_URL}/rest/api/2/issue/NOPE-1", status=status, body="boom")

        with pytest.raises(APIError) as exc_info:
            AtlassianAPI(url=BASE_URL).get("/rest/api/2/issue/NOPE-1")

        assert exc_info.value.code == status
        assert exc_info.value.message == "boom"
        assert str(exc_info.value) == f"Error [{status}] : boom"

    @pytest.mark.parametrize(
        "body, expected",
        [("", None), ("plain text", "plain text"), ("[1, 2]", [1, 2])],
    )
    def test_get_non_object_bodies(self, http, body, expected):
        http.get(f"{BASE_URL}/rest/api/2/thing", body=body)

        assert AtlassianAPI(url=BASE_URL).get("/rest/api/2/thing") == expected

    @pytest.mark.parametrize("method", ["post", "put", "delete"])
    def test_mutating_helpers_decode_json(self, http, method):
        http.add(
            method.upper(),
            f"{BASE_URL}/rest/api/2/thing",
            json={"id": "10000"},
            match=[
                matchers.json_params_matcher({"name": "x"}),
                matchers.query_param_matcher({"notify": "false"}),
            ],
        )
        api = AtlassianAPI(url=BASE_URL)

        result = getattr(api, method)(
            "/rest/api/2/thing", json={"name": "x"}, params={"notify": "false"}
        )

        assert result == {"id": "10000"}

    @pytest.mark.parametrize("method", ["post", "put", "delete"])
    def test_mutating_helpers_return_none_for_empty_body(self, http, method):
        http.add(method.upper(), f"{BASE_URL}/rest/api/2/thing", status=204)

        assert getattr(AtlassianAPI(url=BASE_URL), method)("/rest/api/2/thing") is None

    def test_form_data_is_sent_as_body(self, http):
        http.post(
            f"{BASE_URL}/rest/api/2/thing",
            match=[matchers.urlencoded_params_matcher({"a": "1"})],
        )

        AtlassianAPI(url=BASE_URL).post("/rest/api/2/thing", data={"a": "1"})

    def test_debug_log_does_not_contain_credentials(self, http, caplog, monkeypatch):
        from atlassian import client

        http.get(f"{BASE_URL}/rest/api/2/myself", json={})
        monkeypatch.setattr(client.logger, "disabled", False)
        client.logger.addHandler(caplog.handler)
        try:
            with caplog.at_level(logging.DEBUG, logger=client.logger.name):
                AtlassianAPI(url=BASE_URL, username="alice", password="s3cr3t").get(
                    "/rest/api/2/myself"
                )
                AtlassianAPI(url=BASE_URL, token="tok3n")
        finally:
            client.logger.removeHandler(caplog.handler)

        assert "HTTP: GET -> 200 OK" in caplog.text
        assert "s3cr3t" not in caplog.text
        assert "tok3n" not in caplog.text

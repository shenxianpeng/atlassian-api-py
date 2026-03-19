import pytest
from unittest.mock import MagicMock, patch, Mock
import requests
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

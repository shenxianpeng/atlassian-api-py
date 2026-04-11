from __future__ import annotations

import requests  # type: ignore
import json
from types import SimpleNamespace, TracebackType
from .error import APIError
from .logger import get_logger

logger = get_logger(__name__)
logger.disabled = True


class AtlassianAPI:
    """Base HTTP client shared by Jira, Bitbucket, and Confluence clients.

    The client stores a ``requests.Session``, applies either basic auth or a
    bearer token, appends endpoint paths to the configured base URL, and raises
    :class:`atlassian.error.APIError` for HTTP ``4xx`` and ``5xx`` responses.

    ``get()`` parses JSON into nested ``SimpleNamespace`` objects. Mutating
    helpers return decoded JSON dictionaries when available.
    """

    default_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 60,
        session: requests.Session | None = None,
        token: str | None = None,
    ) -> None:
        """Create a client session for an Atlassian REST API.

        :param url: Base URL of the Atlassian product, for example
            ``https://jira.company.com``. Trailing slashes are removed.
        :type url: str
        :param username: Username for basic authentication. Use together with
            ``password``.
        :type username: str, optional
        :param password: Password for basic authentication. Use together with
            ``username``.
        :type password: str, optional
        :param timeout: Request timeout in seconds.
        :type timeout: int, optional
        :param session: Existing ``requests.Session`` to reuse. When omitted, a
            new session is created.
        :type session: requests.Session, optional
        :param token: Bearer token used to set the ``Authorization`` header.
        :type token: str, optional
        """
        self.url = url.strip("/")
        self.username = username
        self.password = password
        self.timeout = int(timeout)
        if session is None:
            self._session = requests.Session()
        else:
            self._session = session
        if username and password:
            try:
                self._create_basic_session(username, password)
            except Exception as e:
                logger.error(e)
        elif token is not None:
            self._create_token_session(token)

    def __enter__(self) -> AtlassianAPI:
        """Return the client for ``with`` statement usage.

        :return: The API instance.
        :rtype: AtlassianAPI
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the session when leaving a ``with`` block.

        :param exc_type: The exception type (if any).
        :type exc_type: type
        :param exc_val: The exception value (if any).
        :type exc_val: Exception
        :param exc_tb: The traceback object (if any).
        :type exc_tb: traceback
        """
        self.close()

    def _create_basic_session(self, username: str, password: str) -> None:
        """Apply username/password authentication to the current session.

        :param username: The username for authentication.
        :type username: str
        :param password: The password for authentication.
        :type password: str
        """
        self._session.auth = (username, password)

    def _create_token_session(self, token: str) -> None:
        """Apply bearer token authentication to the current session.

        :param token: The bearer token for authentication.
        :type token: str
        """
        self._update_header("Authorization", f"Bearer {token}")

    def _update_header(self, key: str, value: str) -> None:
        """Set or replace a header on the current session.

        :param key: The header key to update.
        :type key: str
        :param value: The value to set for the header key.
        :type value: str
        """
        self._session.headers.update({key: value})

    @staticmethod
    def _response_handler(response: requests.Response) -> dict | None:
        """Decode a response body as JSON.

        :param response: The HTTP response object.
        :type response: requests.Response
        :return: The parsed JSON content, or ``None`` when the response is
            empty or cannot be parsed as JSON.
        :rtype: dict or None
        """
        try:
            return response.json()
        except ValueError:
            logger.debug("Received response with no content.")
            return None
        except Exception as e:
            logger.error(e)
            return None

    def close(self) -> None:
        """Close the underlying ``requests.Session``."""
        self._session.close()

    def request(
        self,
        method: str = "GET",
        path: str = "",
        data: dict | None = None,
        json: object | None = None,
        params: dict | None = None,
    ) -> requests.Response:
        """Send an HTTP request through the configured session.

        :param method: The HTTP method (e.g., "GET", "POST", "PUT", "DELETE").
        :type method: str
        :param path: Endpoint path appended to ``self.url``. Include the leading
            slash, for example ``/rest/api/2/project``.
        :type path: str
        :param data: Form data or bytes to send in the request body.
        :type data: dict or None
        :param json: JSON payload to send in the request body.
        :type json: object or None
        :param params: Query string parameters.
        :type params: dict or None
        :return: The HTTP response object.
        :rtype: requests.Response
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        if path:
            url = self.url + path
        else:
            url = self.url
        response = self._session.request(
            method=method,
            url=url,
            data=data,
            json=json,
            params=params,
            timeout=self.timeout,
        )
        response.encoding = "utf-8"
        logger.debug(f"HTTP: {method} -> {response.status_code} {response.reason}")
        if response.status_code >= 400:
            raise APIError(response.status_code, response.text)
        return response

    def get(
        self,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> SimpleNamespace | str | None:
        """Send a ``GET`` request and parse the response for script-friendly use.

        :param path: Endpoint path appended to the base URL.
        :type path: str
        :param data: Optional request body data.
        :type data: dict or None
        :param params: Query string parameters.
        :type params: dict or None
        :return: A nested ``SimpleNamespace`` for JSON responses, raw text when
            JSON parsing fails, or ``None`` for empty responses.
        :rtype: SimpleNamespace or str or None
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        response = self.request("GET", path, data=data, params=params)
        if not response.text:
            return None
        try:
            text = response.text
            result = json.loads(text, object_hook=lambda d: SimpleNamespace(**d))
            return result
        except Exception as e:
            logger.error(e)
            return response.text

    def post(
        self,
        path: str,
        data: dict | None = None,
        json: object | None = None,
        params: dict | None = None,
    ) -> dict | None:
        """Send a ``POST`` request.

        :param path: Endpoint path appended to the base URL.
        :type path: str
        :param data: Optional request body data.
        :type data: dict or None
        :param json: JSON payload to send in the request body.
        :type json: object or None
        :param params: Query string parameters.
        :type params: dict or None
        :return: Decoded JSON response, or ``None`` for empty/non-JSON responses.
        :rtype: dict or None
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        response = self.request("POST", path, data=data, json=json, params=params)
        return self._response_handler(response)

    def put(
        self,
        path: str,
        data: dict | None = None,
        json: object | None = None,
        params: dict | None = None,
    ) -> dict | None:
        """Send a ``PUT`` request.

        :param path: Endpoint path appended to the base URL.
        :type path: str
        :param data: Optional request body data.
        :type data: dict or None
        :param json: JSON payload to send in the request body.
        :type json: object or None
        :param params: Query string parameters.
        :type params: dict or None
        :return: Decoded JSON response, or ``None`` for empty/non-JSON responses.
        :rtype: dict or None
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        response = self.request("PUT", path, data=data, json=json, params=params)
        return self._response_handler(response)

    def delete(
        self,
        path: str,
        data: dict | None = None,
        json: object | None = None,
        params: dict | None = None,
    ) -> dict | None:
        """Send a ``DELETE`` request.

        :param path: Endpoint path appended to the base URL.
        :type path: str
        :param data: Optional request body data.
        :type data: dict or None
        :param json: JSON payload to send in the request body.
        :type json: object or None
        :param params: Query string parameters.
        :type params: dict or None
        :return: Decoded JSON response, or ``None`` for empty/non-JSON responses.
        :rtype: dict or None
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        response = self.request("DELETE", path, data=data, json=json, params=params)
        return self._response_handler(response)

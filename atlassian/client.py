from __future__ import annotations

import requests  # type: ignore
import json
from types import SimpleNamespace, TracebackType
from .error import APIError
from .logger import get_logger

logger = get_logger(__name__)
logger.disabled = True


class AtlassianAPI:
    """
    Base class for interacting with Atlassian APIs.

    This class provides methods for making HTTP requests (GET, POST, PUT, DELETE)
    and managing authentication sessions.
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
        """
        Initialize the AtlassianAPI instance.

        :param url: The base URL of the Atlassian API.
        :type url: str
        :param username: The username for basic authentication (optional).
        :type username: str, optional
        :param password: The password for basic authentication (optional).
        :type password: str, optional
        :param timeout: The timeout for HTTP requests in seconds (default is 60).
        :type timeout: int, optional
        :param session: A custom requests session (optional).
        :type session: requests.Session, optional
        :param token: The token for bearer authentication (optional).
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
        """
        Enter the runtime context for the API instance.

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
        """
        Exit the runtime context and close the session.

        :param exc_type: The exception type (if any).
        :type exc_type: type
        :param exc_val: The exception value (if any).
        :type exc_val: Exception
        :param exc_tb: The traceback object (if any).
        :type exc_tb: traceback
        """
        self.close()

    def _create_basic_session(self, username: str, password: str) -> None:
        """
        Create a session with basic authentication.

        :param username: The username for authentication.
        :type username: str
        :param password: The password for authentication.
        :type password: str
        """
        self._session.auth = (username, password)

    def _create_token_session(self, token: str) -> None:
        """
        Create a session with bearer token authentication.

        :param token: The bearer token for authentication.
        :type token: str
        """
        self._update_header("Authorization", f"Bearer {token}")

    def _update_header(self, key: str, value: str) -> None:
        """
        Update the headers for the current session.

        :param key: The header key to update.
        :type key: str
        :param value: The value to set for the header key.
        :type value: str
        """
        self._session.headers.update({key: value})

    @staticmethod
    def _response_handler(response: requests.Response) -> dict | None:
        """
        Handle the HTTP response and parse JSON content.

        :param response: The HTTP response object.
        :type response: requests.Response
        :return: The parsed JSON content or None if parsing fails.
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
        """
        Close the current session.

        :return: None
        """
        self._session.close()

    def request(
        self,
        method: str = "GET",
        path: str = "",
        data: dict | None = None,
        json: object | None = None,
        params: dict | None = None,
    ) -> requests.Response:
        """
        Make an HTTP request.

        :param method: The HTTP method (e.g., "GET", "POST", "PUT", "DELETE").
        :type method: str
        :param path: The API endpoint path.
        :type path: str
        :param data: The data to send in the request body (optional).
        :type data: dict or None
        :param json: The JSON payload to send in the request body (optional).
        :type json: object or None
        :param params: The query parameters for the request (optional).
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
        """
        Make a GET request.

        :param path: The API endpoint path.
        :type path: str
        :param data: The data to send in the request body (optional).
        :type data: dict or None
        :param params: The query parameters for the request (optional).
        :type params: dict or None
        :return: The parsed JSON response or raw text if parsing fails.
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
        """
        Make a POST request.

        :param path: The API endpoint path.
        :type path: str
        :param data: The data to send in the request body (optional).
        :type data: dict or None
        :param json: The JSON payload to send in the request body (optional).
        :type json: object or None
        :param params: The query parameters for the request (optional).
        :type params: dict or None
        :return: The parsed JSON response or None if parsing fails.
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
        """
        Make a PUT request.

        :param path: The API endpoint path.
        :type path: str
        :param data: The data to send in the request body (optional).
        :type data: dict or None
        :param json: The JSON payload to send in the request body (optional).
        :type json: object or None
        :param params: The query parameters for the request (optional).
        :type params: dict or None
        :return: The parsed JSON response or None if parsing fails.
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
        """
        Make a DELETE request.

        :param path: The API endpoint path.
        :type path: str
        :param data: The data to send in the request body (optional).
        :type data: dict or None
        :param json: The JSON payload to send in the request body (optional).
        :type json: object or None
        :param params: The query parameters for the request (optional).
        :type params: dict or None
        :return: The parsed JSON response or None if parsing fails.
        :rtype: dict or None
        :raises APIError: If the response status code is 4xx or 5xx.
        """
        response = self.request("DELETE", path, data=data, json=json, params=params)
        return self._response_handler(response)

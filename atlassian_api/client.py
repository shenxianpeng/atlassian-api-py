from __future__ import annotations

import requests  # type: ignore
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from types import SimpleNamespace, TracebackType
from urllib.parse import urlsplit

from .error import APIError, error_for_status
from .logger import get_logger

logger = get_logger(__name__)

#: Host name suffixes of Atlassian Cloud sites.
CLOUD_HOST_SUFFIXES = (".atlassian.net", ".jira.com")

_CLOUD_TOKEN_HINT = (
    "\nHint: Atlassian Cloud API tokens use basic authentication. Pass "
    "username=<your account email> and password=<API token> instead of token=."
)


_HTML_HINT = (
    "Expected {expected} from {url} but received an HTML page. This usually means the "
    "request was redirected to a login or SSO page: check the URL and credentials."
)


def _retry_after_seconds(response: requests.Response) -> float | None:
    """Return the ``Retry-After`` delay in seconds, if the header is usable."""
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def _is_html(response: requests.Response) -> bool:
    """Return whether the response declares an HTML body."""
    return "text/html" in response.headers.get("Content-Type", "").lower()


def is_cloud_url(url: str) -> bool:
    """Return ``True`` when ``url`` points at an Atlassian Cloud site.

    Cloud sites live under ``*.atlassian.net`` (or the legacy ``*.jira.com``),
    and OAuth 2.0 / scoped-token requests go through ``api.atlassian.com``.

    :param url: Base URL of the Atlassian product.
    :type url: str
    :return: Whether the URL is an Atlassian Cloud URL.
    :rtype: bool
    """
    host = (urlsplit(url).hostname or "").lower()
    return host.endswith(CLOUD_HOST_SUFFIXES) or host == "api.atlassian.com"


class AtlassianAPI:
    """Base HTTP client shared by Jira, Bitbucket, and Confluence clients.

    The client stores a ``requests.Session``, applies either basic auth or a
    bearer token, appends endpoint paths to the configured base URL, and raises
    :class:`atlassian_api.error.APIError` for HTTP ``4xx`` and ``5xx`` responses.

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
        verify: bool | str = True,
        proxies: dict | None = None,
        cloud: bool | None = None,
        max_retries: int = 3,
        max_retry_wait: float = 60,
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
        :param verify: SSL certificate verification. Pass ``False`` to disable
            verification (not recommended in production), or a path to a CA
            bundle to use for verification.
        :type verify: bool or str, optional
        :param proxies: Dictionary mapping protocol names to proxy URLs, for
            example ``{"https": "http://proxy.example.com:8080"}``.
        :type proxies: dict, optional
        :param cloud: Whether the server is Atlassian Cloud. When omitted, it
            is detected from the URL (``*.atlassian.net``). Cloud and
            Server/Data Center expose different endpoints for some operations;
            the product clients pick the right one.
        :type cloud: bool, optional
        :param max_retries: How many times to retry a request answered with
            HTTP 429 (any method) or HTTP 503 (``GET`` only). ``0`` disables
            retries.
        :type max_retries: int, optional
        :param max_retry_wait: Longest wait in seconds before a retry. The
            server's ``Retry-After`` is honoured; when it asks for longer, the
            client raises :class:`atlassian_api.error.RateLimitError` instead
            of sleeping (its ``retry_after`` says how long). Without the
            header, waits are 1, 2, 4... seconds, capped at this value.
        :type max_retry_wait: float, optional
        """
        self.url = url.strip("/")
        self.username = username
        self.password = password
        self.timeout = int(timeout)
        self.cloud = is_cloud_url(self.url) if cloud is None else cloud
        self.max_retries = max_retries
        self.max_retry_wait = max_retry_wait
        self._bearer_auth = token is not None and not (username and password)
        if session is None:
            self._session = requests.Session()
        else:
            self._session = session
        self._session.verify = verify
        if proxies is not None:
            self._session.proxies.update(proxies)
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
            if response.text and _is_html(response):
                raise APIError(
                    response.status_code,
                    _HTML_HINT.format(expected="JSON", url=response.url),
                )
            logger.debug("Received response with no content.")
            return None
        except Exception as e:
            logger.error(e)
            return None

    def close(self) -> None:
        """Close the underlying ``requests.Session``."""
        self._session.close()

    def _resolve_url(self, path: str) -> str:
        """Return the absolute URL for ``path``.

        Absolute URLs (for example attachment download links returned by the
        API) are accepted only on the same scheme and host as the client, so
        credentials are never sent to another server.
        """
        if not path.startswith(("http://", "https://")):
            return self.url + path
        target, base = urlsplit(path), urlsplit(self.url)
        if (target.scheme, target.netloc.lower()) != (base.scheme, base.netloc.lower()):
            raise ValueError(f"Refusing to send credentials to another host: {path}")
        return path

    def _retry_delay(
        self, method: str, response: requests.Response, attempt: int
    ) -> float | None:
        """Return how long to wait before retrying, or ``None`` to stop."""
        status = response.status_code
        if status != 429 and not (status == 503 and method.upper() == "GET"):
            return None
        if attempt >= self.max_retries:
            return None
        delay = _retry_after_seconds(response)
        if delay is None:
            return min(2.0**attempt, self.max_retry_wait)
        if delay > self.max_retry_wait:
            return None
        return delay

    def request(
        self,
        method: str = "GET",
        path: str = "",
        data: dict | bytes | None = None,
        json: object | None = None,
        params: dict | None = None,
        files: dict | None = None,
        headers: dict | None = None,
        stream: bool = False,
    ) -> requests.Response:
        """Send an HTTP request through the configured session.

        Requests answered with HTTP 429 (or 503 for ``GET``) are retried, see
        ``max_retries``. Error responses raise a subclass of
        :class:`atlassian_api.error.APIError` that matches the status code,
        such as :class:`~atlassian_api.error.NotFoundError`.

        :param method: The HTTP method (e.g., "GET", "POST", "PUT", "DELETE").
        :type method: str
        :param path: Endpoint path appended to ``self.url``. Include the leading
            slash, for example ``/rest/api/2/project``. An absolute URL on the
            same host is used as is.
        :type path: str
        :param data: Form data or bytes to send in the request body.
        :type data: dict or bytes or None
        :param json: JSON payload to send in the request body.
        :type json: object or None
        :param params: Query string parameters.
        :type params: dict or None
        :param files: Multipart files, as accepted by ``requests``. Pass file
            contents as ``bytes`` so a retried request can resend them.
        :type files: dict or None
        :param headers: Extra headers for this request only.
        :type headers: dict or None
        :param stream: Do not download the body immediately (for large files).
        :type stream: bool
        :return: The HTTP response object.
        :rtype: requests.Response
        :raises APIError: If the response status code is 4xx or 5xx.
        :raises ValueError: If ``path`` is an absolute URL on another host.
        """
        url = self._resolve_url(path)
        attempt = 0
        while True:
            response = self._session.request(
                method=method,
                url=url,
                data=data,
                json=json,
                params=params,
                files=files,
                headers=headers,
                timeout=self.timeout,
                stream=stream,
            )
            response.encoding = "utf-8"
            logger.debug(f"HTTP: {method} -> {response.status_code} {response.reason}")
            delay = self._retry_delay(method, response, attempt)
            if delay is None:
                break
            logger.warning(
                "HTTP %s from %s %s; retrying in %.1fs",
                response.status_code,
                method,
                url,
                delay,
            )
            response.close()
            time.sleep(delay)
            attempt += 1
        if response.status_code >= 400:
            message = response.text
            if response.status_code == 401 and self.cloud and self._bearer_auth:
                message += _CLOUD_TOKEN_HINT
            raise error_for_status(
                response.status_code,
                message,
                retry_after=_retry_after_seconds(response),
            )
        return response

    def _download(
        self,
        url: str,
        path: str | Path | None = None,
        params: dict | None = None,
        reject_html: bool = False,
    ) -> bytes | Path:
        """Download a file from ``url`` (a path or a same-host absolute URL).

        :param url: Endpoint path or absolute URL on the client's host.
        :type url: str
        :param path: Where to stream the file. When omitted, the contents are
            returned.
        :type path: str or pathlib.Path, optional
        :param params: Query string parameters.
        :type params: dict, optional
        :param reject_html: Raise instead of saving an HTML page, for
            downloads that can never be HTML (a login page is).
        :type reject_html: bool
        :return: File contents, or the written path.
        :rtype: bytes or pathlib.Path
        """
        response = self.request("GET", url, params=params, stream=path is not None)
        if reject_html and _is_html(response):
            response.close()
            raise APIError(
                response.status_code,
                _HTML_HINT.format(expected="a file", url=response.url),
            )
        if path is None:
            return response.content
        target = Path(path)
        try:
            with target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    handle.write(chunk)
        finally:
            response.close()
        return target

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
        :raises APIError: If the response status code is 4xx or 5xx, or the
            server answered with an HTML page (typically a login redirect).
        """
        response = self.request("GET", path, data=data, params=params)
        if not response.text:
            return None
        try:
            text = response.text
            result = json.loads(text, object_hook=lambda d: SimpleNamespace(**d))
            return result
        except Exception as e:
            if _is_html(response):
                raise APIError(
                    response.status_code,
                    _HTML_HINT.format(expected="JSON", url=response.url),
                )
            logger.debug("Response is not JSON: %s", e)
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

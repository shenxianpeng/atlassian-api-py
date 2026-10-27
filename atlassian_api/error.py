"""HTTP error helpers used by the Atlassian clients.

``AtlassianAPI.request()`` raises ``APIError`` for HTTP ``4xx`` and ``5xx``
responses. The exception keeps the status code and the response text so callers
can log or branch on the failure.

HTTP response code reference:
https://developer.atlassian.com/server/confluence/http-response-code-definitions/
"""

from __future__ import annotations

_ERROR_CODE_MESSAGE = {
    -1: "Unknown Error Code",
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Time-out",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    416: "Requested range not satisfiable",
    417: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out",
    505: "HTTP Version not supported",
}


class APIError(Exception):
    """Exception raised when an Atlassian REST API request fails.

    :param code: The HTTP status code of the error.
    :type code: int, optional
    :param message: Response body or custom error message. If omitted, a
        default message is selected from the status code.
    :type message: str, optional
    """

    def __init__(self, code: int | None = None, message: str | None = None) -> None:
        """Create an API error with a status code and message.

        :param code: The HTTP status code of the error.
        :type code: int, optional
        :param message: Response body or custom error message.
        :type message: str, optional
        """
        self.code = code
        if message:
            self.message = message
        else:
            self.message = (
                _ERROR_CODE_MESSAGE.get(code, "Unknown Error")
                if code is not None
                else "Unknown Error"
            )

    def __str__(self) -> str:
        """Return a readable ``Error [code] : message`` string.

        :return: A formatted string containing the error code and message.
        :rtype: str
        """
        return "Error [{0}] : {1}".format(self.code, self.message)


class AuthenticationError(APIError):
    """HTTP 401: the credentials are missing or wrong."""


class PermissionDeniedError(APIError):
    """HTTP 403: the user is authenticated but not allowed to do this."""


class NotFoundError(APIError):
    """HTTP 404: the resource does not exist or is not visible to the user."""


class ConflictError(APIError):
    """HTTP 409: the request conflicts with the current state of the resource."""


class RateLimitError(APIError):
    """HTTP 429: too many requests.

    :param retry_after: Seconds the server asked to wait, when it said.
    :type retry_after: float, optional
    """

    def __init__(
        self,
        code: int | None = 429,
        message: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        """Create a rate-limit error."""
        super().__init__(code, message)
        self.retry_after = retry_after


class ServerError(APIError):
    """HTTP 5xx: the server failed to handle the request."""


_ERRORS_BY_CODE: dict[int, type[APIError]] = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
}


def error_for_status(
    code: int, message: str | None = None, retry_after: float | None = None
) -> APIError:
    """Return the most specific :class:`APIError` subclass for a status code.

    Every class returned here is a subclass of :class:`APIError`, so existing
    ``except APIError`` handlers keep catching everything.

    :param code: HTTP status code.
    :type code: int
    :param message: Response body or custom message.
    :type message: str, optional
    :param retry_after: Seconds to wait, for HTTP 429.
    :type retry_after: float, optional
    :return: An exception instance (not raised).
    :rtype: APIError
    """
    if code == 429:
        return RateLimitError(code, message, retry_after=retry_after)
    if code >= 500:
        return ServerError(code, message)
    return _ERRORS_BY_CODE.get(code, APIError)(code, message)

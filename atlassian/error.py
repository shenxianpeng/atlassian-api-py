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

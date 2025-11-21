import pytest
from atlassian.error import APIError


class TestAPIError:
    def test_api_error_with_code_and_message(self):
        error = APIError(code=404, message="Custom error message")
        assert error.code == 404
        assert error.message == "Custom error message"
        assert str(error) == "Error [404] : Custom error message"

    def test_api_error_with_code_only(self):
        error = APIError(code=404)
        assert error.code == 404
        assert error.message == "Not Found"
        assert str(error) == "Error [404] : Not Found"

    def test_api_error_with_unknown_code(self):
        error = APIError(code=999)
        assert error.code == 999
        assert error.message == "Unknown Error"
        assert str(error) == "Error [999] : Unknown Error"

    def test_api_error_with_no_args(self):
        error = APIError()
        assert error.code is None
        assert error.message == "Unknown Error"
        assert str(error) == "Error [None] : Unknown Error"

    def test_api_error_common_codes(self):
        # Test some common HTTP status codes
        error_200 = APIError(code=200)
        assert error_200.message == "OK"

        error_400 = APIError(code=400)
        assert error_400.message == "Bad Request"

        error_401 = APIError(code=401)
        assert error_401.message == "Unauthorized"

        error_403 = APIError(code=403)
        assert error_403.message == "Forbidden"

        error_500 = APIError(code=500)
        assert error_500.message == "Internal Server Error"

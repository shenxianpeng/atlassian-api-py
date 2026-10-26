"""Shared test fixtures."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def no_retry_sleep():
    """Never really sleep between retries; tests can inspect the calls."""
    with patch("atlassian_api.client.time.sleep") as sleep:
        yield sleep

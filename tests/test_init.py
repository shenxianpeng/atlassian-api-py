import importlib
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

import pytest

import atlassian
from atlassian.bitbucket import Bitbucket
from atlassian.confluence import Confluence
from atlassian.jira import Jira


class TestPackage:
    @pytest.fixture(autouse=True)
    def restore_package(self):
        yield
        # Re-import with the real metadata so later tests see the real version.
        importlib.reload(atlassian)

    def test_public_api(self):
        assert atlassian.__all__ == ["Jira", "Bitbucket", "Confluence", "__version__"]
        assert atlassian.Jira is Jira
        assert atlassian.Bitbucket is Bitbucket
        assert atlassian.Confluence is Confluence

    def test_version_from_package_metadata(self):
        with patch("importlib.metadata.version", return_value="9.8.7") as version:
            importlib.reload(atlassian)
        version.assert_called_once_with("atlassian-api-py")
        assert atlassian.__version__ == "9.8.7"

    def test_version_unknown_when_package_is_not_installed(self):
        with patch(
            "importlib.metadata.version",
            side_effect=PackageNotFoundError("atlassian-api-py"),
        ):
            importlib.reload(atlassian)
        assert atlassian.__version__ == "unknown"

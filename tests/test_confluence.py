import pytest
from unittest.mock import MagicMock
from atlassian.confluence import Confluence


class TestConfluence:
    @pytest.fixture
    def confluence(self):
        confluence = Confluence(url="https://fake_url")
        confluence.get = MagicMock()
        confluence.put = MagicMock()
        confluence.post = MagicMock()
        confluence.delete = MagicMock()
        return confluence

    def test_get_content(self, confluence):
        confluence.get_content()
        confluence.get.assert_called_with("/rest/api/content")

    def test_create_content(self, confluence):
        confluence.create_content("Test Page", "TEST_SPACE", "Body Value")
        confluence.post.assert_called_with(
            "/rest/api/content",
            json={
                "type": "page",
                "title": "Test Page",
                "space": {"key": "TEST_SPACE"},
                "body": {
                    "storage": {"value": "Body Value", "representation": "storage"}
                },
            },
        )

    def test_create_content_with_ancestors_id(self, confluence):
        confluence.create_content("Test Page", "TEST_SPACE", "Body Value", 1234)
        confluence.post.assert_called_with(
            "/rest/api/content",
            json={
                "type": "page",
                "title": "Test Page",
                "ancestors": [{"id": 1234}],
                "space": {"key": "TEST_SPACE"},
                "body": {
                    "storage": {"value": "Body Value", "representation": "storage"}
                },
            },
        )

    def test_update_content(self, confluence):
        mock_current = MagicMock()
        mock_current.version.number = 1
        confluence.get_content_by_id = MagicMock(return_value=mock_current)
        
        confluence.update_content(123, "Test Page", "Body Value")
        
        confluence.get_content_by_id.assert_called_with(123)
        confluence.put.assert_called_with(
            "/rest/api/content/123",
            json={
                "version": {"number": 2},
                "title": "Test Page",
                "type": "page",
                "body": {
                    "storage": {"value": "Body Value", "representation": "storage"}
                },
            },
        )

    def test_delete_content(self, confluence):
        confluence.delete_content(123)
        confluence.delete.assert_called_with("/rest/api/content/123")

    def test_get_content_by_id(self, confluence):
        confluence.get_content_by_id(123)
        confluence.get.assert_called_with("/rest/api/content/123")

    def test_get_content_history(self, confluence):
        confluence.get_content_history(123)
        confluence.get.assert_called_with("/rest/api/content/123/history")

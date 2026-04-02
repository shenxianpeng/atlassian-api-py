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
        confluence.update_content(123, "Test Page", "Body Value")
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

    def test_get_spaces(self, confluence):
        confluence.get_spaces()
        confluence.get.assert_called_with(
            "/rest/api/space", params={"start": 0, "limit": 25}
        )

    def test_get_spaces_custom_params(self, confluence):
        confluence.get_spaces(start=25, limit=50)
        confluence.get.assert_called_with(
            "/rest/api/space", params={"start": 25, "limit": 50}
        )

    def test_get_space(self, confluence):
        confluence.get_space("TEST_SPACE")
        confluence.get.assert_called_with("/rest/api/space/TEST_SPACE")

    def test_get_content_by_space(self, confluence):
        confluence.get_content_by_space("TEST_SPACE")
        confluence.get.assert_called_with(
            "/rest/api/content",
            params={"spaceKey": "TEST_SPACE", "type": "page", "start": 0, "limit": 25},
        )

    def test_get_content_by_space_blogpost(self, confluence):
        confluence.get_content_by_space(
            "TEST_SPACE", content_type="blogpost", start=10, limit=5
        )
        confluence.get.assert_called_with(
            "/rest/api/content",
            params={
                "spaceKey": "TEST_SPACE",
                "type": "blogpost",
                "start": 10,
                "limit": 5,
            },
        )

    def test_search_content(self, confluence):
        confluence.search_content("space=TEST AND type=page")
        confluence.get.assert_called_with(
            "/rest/api/content/search",
            params={"cql": "space=TEST AND type=page", "start": 0, "limit": 25},
        )

    def test_search_content_custom_params(self, confluence):
        confluence.search_content("title=Hello", start=5, limit=10)
        confluence.get.assert_called_with(
            "/rest/api/content/search",
            params={"cql": "title=Hello", "start": 5, "limit": 10},
        )

    def test_get_child_pages(self, confluence):
        confluence.get_child_pages(123)
        confluence.get.assert_called_with(
            "/rest/api/content/123/child/page",
            params={"start": 0, "limit": 25},
        )

    def test_get_child_pages_custom_params(self, confluence):
        confluence.get_child_pages(456, start=10, limit=5)
        confluence.get.assert_called_with(
            "/rest/api/content/456/child/page",
            params={"start": 10, "limit": 5},
        )

    def test_get_attachments(self, confluence):
        confluence.get_attachments(123)
        confluence.get.assert_called_with("/rest/api/content/123/child/attachment")

    def test_get_labels(self, confluence):
        confluence.get_labels(123)
        confluence.get.assert_called_with("/rest/api/content/123/label")

    def test_add_label(self, confluence):
        confluence.add_label(123, "my-label")
        confluence.post.assert_called_with(
            "/rest/api/content/123/label",
            json=[{"prefix": "global", "name": "my-label"}],
        )

    def test_remove_label(self, confluence):
        confluence.remove_label(123, "my-label")
        confluence.delete.assert_called_with(
            "/rest/api/content/123/label",
            params={"name": "my-label"},
        )

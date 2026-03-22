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
        # get_content_version calls get_content_history internally; mock it directly
        confluence.get_content_version = MagicMock(return_value=5)
        confluence.update_content(123, "Test Page", "Body Value")
        confluence.put.assert_called_with(
            "/rest/api/content/123",
            json={
                "version": {"number": 6},
                "title": "Test Page",
                "type": "page",
                "body": {
                    "storage": {"value": "Body Value", "representation": "storage"}
                },
            },
        )

    def test_update_content_version_fetch_failure_raises(self, confluence):
        from atlassian.error import APIError

        confluence.get_content_version = MagicMock(return_value=None)
        with pytest.raises(APIError):
            confluence.update_content(999, "Title", "Body")

    def test_delete_content(self, confluence):
        confluence.delete_content(123)
        confluence.delete.assert_called_with("/rest/api/content/123")

    def test_get_content_by_id(self, confluence):
        confluence.get_content_by_id(123)
        confluence.get.assert_called_with("/rest/api/content/123")

    def test_get_content_history(self, confluence):
        confluence.get_content_history(123)
        confluence.get.assert_called_with("/rest/api/content/123/history")

    def test_get_content_version_returns_number(self, confluence):
        from types import SimpleNamespace

        mock_history = SimpleNamespace(lastUpdated=SimpleNamespace(number=7))
        confluence.get = MagicMock(return_value=mock_history)
        result = confluence.get_content_version(123)
        assert result == 7

    def test_get_content_version_returns_none_on_missing_attr(self, confluence):
        from types import SimpleNamespace

        confluence.get = MagicMock(return_value=SimpleNamespace())
        result = confluence.get_content_version(123)
        assert result is None

    def test_get_content_version_returns_none_on_none_response(self, confluence):
        confluence.get = MagicMock(return_value=None)
        result = confluence.get_content_version(123)
        assert result is None

    # ------------------------------------------------------------------ #
    # Search & spaces                                                      #
    # ------------------------------------------------------------------ #

    def test_search_content(self, confluence):
        confluence.search_content('type=page AND space="TS"')
        confluence.get.assert_called_with(
            "/rest/api/content/search",
            params={"cql": 'type=page AND space="TS"', "limit": 25},
        )

    def test_get_space(self, confluence):
        confluence.get_space("MYSPACE")
        confluence.get.assert_called_with("/rest/api/space/MYSPACE")

    def test_list_spaces(self, confluence):
        confluence.list_spaces()
        confluence.get.assert_called_with("/rest/api/space", params={"limit": 25})

    # ------------------------------------------------------------------ #
    # Page hierarchy                                                       #
    # ------------------------------------------------------------------ #

    def test_get_page_children(self, confluence):
        confluence.get_page_children(123)
        confluence.get.assert_called_with("/rest/api/content/123/child/page")

    def test_get_page_ancestors(self, confluence):
        confluence.get_page_ancestors(123)
        confluence.get.assert_called_with("/rest/api/content/123/ancestor")

    def test_move_page_append(self, confluence):
        confluence.move_page(10, 20)
        confluence.put.assert_called_with("/rest/api/content/10/move/append/20")

    def test_move_page_before(self, confluence):
        confluence.move_page(10, 20, position="before")
        confluence.put.assert_called_with("/rest/api/content/10/move/before/20")

    def test_move_page_invalid_position_raises(self, confluence):
        with pytest.raises(ValueError):
            confluence.move_page(10, 20, position="invalid")

    # ------------------------------------------------------------------ #
    # Attachments                                                          #
    # ------------------------------------------------------------------ #

    def test_get_attachments(self, confluence):
        confluence.get_attachments(123)
        confluence.get.assert_called_with("/rest/api/content/123/child/attachment")

    def test_delete_attachment(self, confluence):
        confluence.delete_attachment("att-456")
        confluence.delete.assert_called_with("/rest/api/content/att-456")

    def test_add_attachment(self, confluence):
        confluence.upload = MagicMock(return_value={"id": "1"})
        confluence.add_attachment(123, "/tmp/file.txt")
        confluence.upload.assert_called_with(
            "/rest/api/content/123/child/attachment",
            "/tmp/file.txt",
            "application/octet-stream",
        )

    # ------------------------------------------------------------------ #
    # Labels                                                               #
    # ------------------------------------------------------------------ #

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
            "/rest/api/content/123/label", params={"name": "my-label"}
        )

    # ------------------------------------------------------------------ #
    # Comments                                                             #
    # ------------------------------------------------------------------ #

    def test_get_comments(self, confluence):
        confluence.get_comments(123)
        confluence.get.assert_called_with("/rest/api/content/123/child/comment")

    def test_add_comment(self, confluence):
        confluence.add_comment(123, "<p>Hello</p>")
        args, kwargs = confluence.post.call_args
        assert args[0] == "/rest/api/content"
        assert kwargs["json"]["type"] == "comment"
        assert kwargs["json"]["container"]["id"] == 123
        assert kwargs["json"]["body"]["storage"]["value"] == "<p>Hello</p>"

    def test_delete_comment(self, confluence):
        confluence.delete_comment(999)
        confluence.delete.assert_called_with("/rest/api/content/999")

    # ------------------------------------------------------------------ #
    # Restrictions & discovery                                             #
    # ------------------------------------------------------------------ #

    def test_get_content_restrictions(self, confluence):
        confluence.get_content_restrictions(123)
        confluence.get.assert_called_with("/rest/api/content/123/restriction")

    def test_get_content_by_title(self, confluence):
        confluence.get_content_by_title("MYSPACE", "My Page")
        confluence.get.assert_called_with(
            "/rest/api/content",
            params={"spaceKey": "MYSPACE", "title": "My Page", "type": "page"},
        )

    def test_search_content_by_label(self, confluence):
        confluence.search_content_by_label("release-notes")
        confluence.get.assert_called_with(
            "/rest/api/content",
            params={"label": "release-notes", "type": "page", "limit": 25},
        )

    def test_search_content_by_label_with_space(self, confluence):
        confluence.search_content_by_label("release-notes", space_key="TS")
        args, kwargs = confluence.get.call_args
        assert kwargs["params"]["spaceKey"] == "TS"

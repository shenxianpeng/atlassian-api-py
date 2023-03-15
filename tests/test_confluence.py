import pytest
from unittest.mock import MagicMock
from atlassian.confluence import Confluence


class TestConfluence:
    @pytest.fixture
    def confluence(self):
        confluence = Confluence(url="https://fake_url")
        confluence.get = MagicMock()
        confluence.post = MagicMock()
        return confluence

    def test_get_content(self, confluence):
        confluence.get_content()
        confluence.get.assert_called_with('/rest/api/content')

    def test_get_content_by_id(self, confluence):
        confluence.get_content_by_id(123)
        confluence.get.assert_called_with('/rest/api/content/123')

    def test_create_content(self, confluence):
        confluence.create_content('Test Page', 'TEST_SPACE')
        confluence.post.assert_called_with('/rest/api/content', json={
            "type": "page",
            "status": "current",
            "title": "Test Page",
            "space":{"key":"TEST_SPACE"},
        })

from atlassian.client import AtlassianAPI
from unittest.mock import patch, MagicMock
from atlassian.confluence import Confluence


class TestConfluence(AtlassianAPI):

    @patch.object(Confluence, "get")
    def test_successful_get_request(self, mock_get):
        confluence = Confluence(url="https://fake_url")
        mock_response = MagicMock(status_code=200, json=lambda: {"content": "example"})
        mock_get.return_value = mock_response
        result = confluence.get_content()
        self.assertEqual(result, {"content": "example"})

    @patch.object(Confluence, "get")
    def test_failed_get_request(self, mock_get):
        confluence = Confluence(url="https://fake_url")
        mock_get.side_effect = Exception("Network error")
        result = confluence.get_content()
        self.assertEqual(result, {})

    @patch.object(Confluence, "get")
    def test_empty_response_from_server(self, mock_get):
        confluence = Confluence(url="https://fake_url")
        mock_response = MagicMock(status_code=200, json=lambda: None)
        mock_get.return_value = mock_response
        result = confluence.get_content()
        self.assertEqual(result, {})

    @patch.object(Confluence, "get")
    def test_non_200_status_code_response_from_server(self, mock_get):
        confluence = Confluence(url="https://fake_url")
        mock_response = MagicMock(status_code=404, json=lambda: {"error": "Not found"})
        mock_get.return_value = mock_response
        result = confluence.get_content()
        self.assertEqual(result, {})

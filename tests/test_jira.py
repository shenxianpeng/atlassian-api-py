import unittest
from unittest.mock import patch, Mock
from atlassian.jira import Jira


class TestJiraIssue(unittest.TestCase):

    @patch.object(Jira, "get")
    def test_issue_retrieval_valid_key(self, mock_get):
        jira = Jira(url="https://fake_url")
        issue_key = "TEST-1"
        mock_response = {"key": issue_key, "fields": {"summary": "Test issue"}}
        mock_get.return_value = mock_response
        result = jira.issue(issue_key)
        self.assertEqual(result, mock_response)

    @patch.object(Jira, "get")
    def test_issue_retrieval_invalid_key(self, mock_get):
        jira = Jira(url="https://fake_url")
        issue_key = "INVALID-KEY"
        mock_get.return_value = None
        result = jira.issue(issue_key)
        self.assertEqual(result, {})

    @patch.object(Jira, "get")
    def test_issue_retrieval_none_key(self, mock_get):
        jira = Jira(url="https://fake_url")
        issue_key = None
        mock_get.return_value = None
        result = jira.issue(issue_key)
        self.assertEqual(result, {})

    @patch.object(Jira, "get")
    def test_issue_retrieval_empty_key(self, mock_get):
        jira = Jira(url="https://fake_url")
        issue_key = ""
        mock_get.return_value = None
        result = jira.issue(issue_key)
        self.assertEqual(result, {})

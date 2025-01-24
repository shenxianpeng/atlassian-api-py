import pytest
from unittest.mock import MagicMock
from atlassian.jira import Jira


class TestJira:
    @pytest.fixture
    def jira(self):
        jira = Jira(url="https://fake_url")
        jira.get = MagicMock()
        jira.put = MagicMock()
        jira.post = MagicMock()
        jira.delete = MagicMock()

        return jira

    def test_issue(self, jira):
        jira.issue("TEST-1")
        jira.get.assert_called_once_with("/rest/api/2/issue/TEST-1")

    def test_issue_changelog(self, jira):
        jira.issue_changelog("TEST-1")
        jira.get.assert_called_once_with(
            "/rest/api/2/issue/TEST-1?expand=changelog&fields=summary"
        )

    def test_update_issue_description(self, jira):
        jira.update_issue_description("TEST-1", "New description")
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={"fields": {"description": "New description"}},
        )

    def test_update_issue_label(self, jira):
        jira.update_issue_label("TEST-1", add_labels=["label1", "label2"])
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={"update": {"labels": [{"add": "label1"}, {"add": "label2"}]}},
        )

    def test_update_issue_label_remove(self, jira):
        jira.update_issue_label("TEST-1", remove_labels=["label1", "label2"])
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={"update": {"labels": [{"remove": "label1"}, {"remove": "label2"}]}},
        )

    def test_update_issue_component(self, jira):
        jira.update_issue_component(
            "TEST-1", add_components=["component1", "component2"]
        )
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={
                "update": {
                    "components": [
                        {"add": {"name": "component1"}},
                        {"add": {"name": "component2"}},
                    ]
                }
            },
        )

    def test_update_field(self, jira):
        jira.update_field("TEST-1", "summary", "New summary")
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={"update": {"summary": [{"add": {"name": "New summary"}}]}},
        )

    def test_add_issue_comment(self, jira):
        jira.add_issue_comment("TEST-1", "New comment")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue/TEST-1/comment", json={"body": "New comment"}
        )

    def test_delete_issue_comment(self, jira):
        jira.delete_issue_comment("TEST-1", "1")
        jira.delete.assert_called_once_with("/rest/api/2/issue/TEST-1/comment/1")

    def test_link_issue_as(self, jira):
        jira.link_issue_as("Dependence", "TEST-1", "TEST-2")
        jira.post.assert_called_once_with(
            "/rest/api/2/issueLink",
            json={
                "type": {"name": "Dependence"},
                "inwardIssue": {"key": "TEST-1"},
                "outwardIssue": {"key": "TEST-2"},
            },
        )

    def test_create_issue(self, jira):
        jira.create_issue("TEST", "New issue")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue", json={"fields": "TEST", "update": "New issue"}
        )

    def test_create_task(self, jira):
        jira.create_task("TEST", "New task")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue",
            json={
                "fields": {
                    "project": {"key": "TEST"},
                    "summary": "New task",
                    "issuetype": {"id": 10},
                    "assignee": {"key": None, "name": None},
                    "customfield_11386": {"key": None, "name": None},
                    "priority": {"id": "4"},
                    "labels": None,
                    "components": None,
                }
            },
        )

    def test_create_sub_task(self, jira):
        jira.create_sub_task("TEST-1", "New subtask")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue",
            json={
                "fields": {
                    "project": {"key": "TEST-1"},
                    "parent": {"key": "New subtask"},
                    "summary": None,
                    "issuetype": {"id": 20},
                    "assignee": {"key": None, "name": None},
                    "priority": {"id": "4"},
                    "description": None,
                    "labels": None,
                    "customfield_13430": {"value": "Testing / Debugging"},
                    "fixVersions": [{"name": None}],
                }
            },
        )

    def test_update_custom_field(self, jira):
        jira.update_custom_field("TEST-1", "customfield_11386", "New value")
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1",
            json={"fields": {"customfield_11386": "New value"}},
        )

    def test_assign_issue(self, jira):
        jira.assign_issue("TEST-1", "developer")
        jira.put.assert_called_once_with(
            "/rest/api/2/issue/TEST-1/assignee", json={"name": "developer"}
        )

    def test_add_issue_watcher(self, jira):
        jira.add_issue_watcher("TEST-1", "developer")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue/TEST-1/watchers", json="developer"
        )

    def test_issue_transition(self, jira):
        jira.issue_transition("TEST-1", "1")
        jira.post.assert_called_once_with(
            "/rest/api/2/issue/TEST-1/transitions", json={"transition": {"id": "1"}}
        )

    def test_get_transitions(self, jira):
        jira.get_transitions("TEST-1")
        jira.get.assert_called_once_with("/rest/api/2/issue/TEST-1/transitions")

    def test_search_issue_with_jql(self, jira):
        jira.search_issue_with_jql("project = TEST")
        jira.post.assert_called_once_with(
            "/rest/api/2/search",
            json={
                "jql": "project = TEST",
                "startAt": 0,
                "maxResults": 1000,
                "fields": ["summary", "status", "issuetype", "fixVersions"],
            },
        )

    def test_get_project_components(self, jira):
        jira.get_project_components("TEST")
        jira.get.assert_called_once_with("/rest/api/2/project/TEST/components")

    def test_user(self, jira):
        jira.user("developer")
        jira.get.assert_called_once_with("/rest/api/2/user?username=developer")

    def test_get_dev_status(self, jira):
        jira.get_dev_status("TEST-1")
        jira.get.assert_called_once_with(
            "/rest/dev-status/1.0/issue/detail?issueId=TEST-1&applicationType=stash&dataType=repository"
        )

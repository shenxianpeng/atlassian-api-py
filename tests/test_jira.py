import pytest
from unittest.mock import MagicMock
from atlassian.jira import Jira


class TestJira:
    @pytest.fixture
    def jira(self):
        jira_client = Jira(url="https://fake_url")
        jira_client.get = MagicMock()
        jira_client.put = MagicMock()
        jira_client.post = MagicMock()
        jira_client.delete = MagicMock()
        return jira_client

    def test_issue(self, jira):
        jira.issue("TEST-123")
        jira.get.assert_called_with("/rest/api/2/issue/TEST-123")

    def test_issue_changelog(self, jira):
        jira.issue_changelog("TEST-456")
        jira.get.assert_called_with(
            "/rest/api/2/issue/TEST-456?expand=changelog&fields=summary"
        )

    def test_update_issue_label_add_only(self, jira):
        jira.update_issue_label("TEST-1", add_labels=["label1", "label2"])
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-1"
        assert "update" in kwargs["json"]
        assert "labels" in kwargs["json"]["update"]

    def test_update_issue_label_remove_only(self, jira):
        jira.update_issue_label("TEST-1", remove_labels=["old-label"])
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-1"
        assert "update" in kwargs["json"]
        assert "labels" in kwargs["json"]["update"]

    def test_update_issue_label_add_and_remove(self, jira):
        jira.update_issue_label("TEST-1", add_labels=["new"], remove_labels=["old"])
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-1"
        assert "update" in kwargs["json"]
        assert "labels" in kwargs["json"]["update"]

    def test_update_issue_label_no_changes(self, jira):
        # Call with None for both parameters
        jira.update_issue_label("TEST-1")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-1"
        # Should pass empty label_data dict
        assert kwargs["json"] == {}

    def test_update_issue_component_add_only(self, jira):
        jira.update_issue_component("TEST-2", add_components=["comp1"])
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-2"
        assert "update" in kwargs["json"]
        assert "components" in kwargs["json"]["update"]

    def test_update_issue_component_remove_only(self, jira):
        jira.update_issue_component("TEST-2", remove_components=["old-comp"])
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-2"
        assert "update" in kwargs["json"]

    def test_update_issue_component_add_and_remove(self, jira):
        jira.update_issue_component(
            "TEST-2", add_components=["new"], remove_components=["old"]
        )
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-2"
        assert "update" in kwargs["json"]

    def test_update_issue_component_no_changes(self, jira):
        # Call with None for both parameters
        jira.update_issue_component("TEST-2")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-2"
        # Should pass empty component_data dict
        assert kwargs["json"] == {}

    def test_update_issue_description(self, jira):
        jira.update_issue_description("TEST-3", "New description")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-3"
        assert kwargs["json"]["fields"]["description"] == "New description"

    def test_update_field_with_add(self, jira):
        jira.update_field("TEST-4", "customfield_123", add="value1")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-4"
        assert "update" in kwargs["json"]

    def test_update_field_with_remove(self, jira):
        jira.update_field("TEST-4", "customfield_123", remove="value2")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-4"
        assert "update" in kwargs["json"]

    def test_update_field_with_add_and_remove(self, jira):
        jira.update_field("TEST-4", "customfield_123", add="new", remove="old")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-4"
        assert "update" in kwargs["json"]

    def test_add_issue_comment(self, jira):
        jira.add_issue_comment("TEST-5", "This is a comment")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue/TEST-5/comment"
        assert kwargs["json"]["body"] == "This is a comment"

    def test_delete_issue_comment(self, jira):
        jira.delete_issue_comment("TEST-6", "12345")
        jira.delete.assert_called_with("/rest/api/2/issue/TEST-6/comment/12345")

    def test_link_issue_as(self, jira):
        jira.link_issue_as(
            type_name="Dependence", inward_issue="TEST-1", outward_issue="TEST-2"
        )
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issueLink"
        assert kwargs["json"]["type"]["name"] == "Dependence"
        assert kwargs["json"]["inwardIssue"]["key"] == "TEST-1"
        assert kwargs["json"]["outwardIssue"]["key"] == "TEST-2"

    def test_delete_issue_link(self, jira):
        jira.delete_issue_link("54321")
        jira.delete.assert_called_with("/rest/api/2/issueLink/54321")

    def test_create_issue(self, jira):
        fields = {"project": {"key": "TEST"}, "summary": "New issue"}
        jira.create_issue(fields)
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue"
        assert kwargs["json"]["fields"] == fields

    def test_create_issue_with_update(self, jira):
        fields = {"project": {"key": "TEST"}, "summary": "New issue"}
        update = {"worklog": [{"add": {"timeSpent": "1h"}}]}
        jira.create_issue(fields, update=update)
        args, kwargs = jira.post.call_args
        assert kwargs["json"]["fields"] == fields
        assert kwargs["json"]["update"] == update

    def test_create_task(self, jira):
        jira.create_task(
            project_key="PROJ",
            summary="Task summary",
            assignee="user1",
            owner="owner1",
            labels=["label1"],
            components=[{"name": "comp1"}],
            issue_type=10,
        )
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue"
        assert kwargs["json"]["fields"]["project"]["key"] == "PROJ"
        assert kwargs["json"]["fields"]["summary"] == "Task summary"

    def test_create_sub_task(self, jira):
        jira.create_sub_task(
            project_key="PROJ",
            parent_issue_key="PROJ-1",
            summary="Subtask summary",
            fix_version="1.0",
            assignee="user1",
            description="Description",
            labels=["label1"],
            issue_type=20,
        )
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue"
        assert kwargs["json"]["fields"]["project"]["key"] == "PROJ"
        assert kwargs["json"]["fields"]["parent"]["key"] == "PROJ-1"

    def test_create_sub_task_with_team(self, jira):
        jira.create_sub_task(
            project_key="PROJ",
            parent_issue_key="PROJ-1",
            summary="Subtask summary",
            fix_version="1.0",
            assignee="user1",
            description="Description",
            labels=["label1"],
            team="TeamA",
            issue_type=20,
        )
        args, kwargs = jira.post.call_args
        assert "customfield_11360" in kwargs["json"]["fields"]

    def test_update_custom_field_single_arg(self, jira):
        jira.update_custom_field("TEST-7", "customfield_123", "value1")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-7"
        assert kwargs["json"]["fields"]["customfield_123"] == "value1"

    def test_update_custom_field_two_args(self, jira):
        jira.update_custom_field("TEST-7", "customfield_123", "key1", "value1")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-7"
        assert kwargs["json"]["fields"]["customfield_123"] == {"key1": "value1"}

    def test_update_custom_field_too_many_args(self, jira):
        with pytest.raises(AttributeError):
            jira.update_custom_field(
                "TEST-7", "customfield_123", "arg1", "arg2", "arg3"
            )

    def test_assign_issue_with_assignee(self, jira):
        jira.assign_issue("TEST-8", assignee="user1")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-8/assignee"
        assert kwargs["json"]["name"] == "user1"

    def test_assign_issue_without_assignee(self, jira):
        jira.assign_issue("TEST-8")
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/issue/TEST-8/assignee"
        assert kwargs["json"]["name"] == -1

    def test_add_issue_watcher(self, jira):
        jira.add_issue_watcher("TEST-9", "watcher1")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue/TEST-9/watchers"
        assert kwargs["json"] == "watcher1"

    def test_issue_transition(self, jira):
        jira.issue_transition("TEST-10", transition_id="51")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue/TEST-10/transitions"
        assert kwargs["json"]["transition"]["id"] == "51"

    def test_get_transitions(self, jira):
        jira.get_transitions("TEST-11")
        jira.get.assert_called_with("/rest/api/2/issue/TEST-11/transitions")

    def test_search_issue_with_jql(self, jira):
        jira.post = MagicMock(
            return_value={
                "total": 2,
                "maxResults": 50,
                "issues": [{"key": "TEST-1"}, {"key": "TEST-2"}],
            }
        )
        result = jira.search_issue_with_jql("project=TEST")
        assert len(result) == 2
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/search"
        assert kwargs["json"]["jql"] == "project=TEST"

    def test_search_issue_with_jql_pagination(self, jira):
        # Mock response that requires pagination
        responses = [
            {
                "total": 150,
                "maxResults": 100,
                "issues": [{"key": f"TEST-{i}"} for i in range(100)],
            },
            {
                "total": 150,
                "maxResults": 100,
                "issues": [{"key": f"TEST-{i}"} for i in range(100, 150)],
            },
        ]
        jira.post = MagicMock(side_effect=responses)
        result = jira.search_issue_with_jql("project=TEST")
        assert len(result) == 150

    def test_search_issue_with_jql_empty_response(self, jira):
        jira.post = MagicMock(return_value={})
        result = jira.search_issue_with_jql("project=NONE")
        assert result == []

    def test_get_project_components(self, jira):
        jira.get_project_components("PROJ")
        jira.get.assert_called_with("/rest/api/2/project/PROJ/components")

    def test_user(self, jira):
        jira.user("testuser")
        jira.get.assert_called_with("/rest/api/2/user?username=testuser")

    def test_get_dev_status(self, jira):
        jira.get_dev_status("12345")
        jira.get.assert_called_with(
            "/rest/dev-status/1.0/issue/detail?issueId=12345&applicationType=stash&dataType=repository"
        )

    def test_get_dev_status_custom_params(self, jira):
        jira.get_dev_status("12345", app_type="custom", data_type="branch")
        jira.get.assert_called_with(
            "/rest/dev-status/1.0/issue/detail?issueId=12345&applicationType=custom&dataType=branch"
        )

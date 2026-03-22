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

    # ------------------------------------------------------------------ #
    # DeprecationWarning                                                   #
    # ------------------------------------------------------------------ #

    def test_create_task_emits_deprecation_warning(self, jira):
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            jira.create_task(project_key="PROJ", summary="s", assignee="a", owner="o")
        assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_create_sub_task_emits_deprecation_warning(self, jira):
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            jira.create_sub_task(
                project_key="PROJ",
                parent_issue_key="PROJ-1",
                summary="s",
                fix_version="1.0",
                assignee="a",
                description="d",
                labels=[],
            )
        assert any(issubclass(x.category, DeprecationWarning) for x in w)

    # ------------------------------------------------------------------ #
    # _paged_post                                                          #
    # ------------------------------------------------------------------ #

    def test_paged_post_single_page(self, jira):
        jira.post = MagicMock(
            return_value={"values": [1, 2, 3], "total": 3, "maxResults": 50}
        )
        result = jira._paged_post(
            "/rest/agile/1.0/board/1/sprint", {}, result_key="values"
        )
        assert result == [1, 2, 3]

    def test_paged_post_multiple_pages(self, jira):
        jira.post = MagicMock(
            side_effect=[
                {"values": list(range(50)), "total": 75, "maxResults": 50},
                {"values": list(range(25)), "total": 75, "maxResults": 50},
            ]
        )
        result = jira._paged_post(
            "/rest/agile/1.0/board/1/sprint", {}, result_key="values"
        )
        assert len(result) == 75

    def test_paged_post_empty_response(self, jira):
        jira.post = MagicMock(return_value={"values": [], "total": 0, "maxResults": 50})
        result = jira._paged_post(
            "/rest/agile/1.0/board/1/sprint", {}, result_key="values"
        )
        assert result == []

    # ------------------------------------------------------------------ #
    # Agile                                                                #
    # ------------------------------------------------------------------ #

    def test_get_boards(self, jira):
        jira.get_boards()
        jira.get.assert_called_with(
            "https://fake_url/rest/agile/1.0/board", params=None
        )

    def test_get_boards_with_project(self, jira):
        jira.get_boards(project_key="PROJ")
        args, kwargs = jira.get.call_args
        assert kwargs["params"]["projectKeyOrId"] == "PROJ"

    def test_get_board(self, jira):
        jira.get_board(42)
        jira.get.assert_called_with("https://fake_url/rest/agile/1.0/board/42")

    def test_get_sprints(self, jira):
        jira.get_sprints(1)
        jira.get.assert_called_with(
            "https://fake_url/rest/agile/1.0/board/1/sprint", params=None
        )

    def test_get_sprints_with_state(self, jira):
        jira.get_sprints(1, state="active")
        args, kwargs = jira.get.call_args
        assert kwargs["params"]["state"] == "active"

    def test_get_active_sprint(self, jira):
        jira.get_active_sprint(1)
        args, kwargs = jira.get.call_args
        assert kwargs["params"]["state"] == "active"

    def test_get_sprint_issues(self, jira):
        jira.get_sprint_issues(10)
        jira.get.assert_called_with(
            "https://fake_url/rest/agile/1.0/sprint/10/issue",
            params={"maxResults": 50},
        )

    def test_create_sprint(self, jira):
        jira.create_sprint(1, "Sprint 1")
        args, kwargs = jira.post.call_args
        assert args[0] == "https://fake_url/rest/agile/1.0/sprint"
        assert kwargs["json"]["name"] == "Sprint 1"
        assert kwargs["json"]["originBoardId"] == 1

    def test_update_sprint_valid_state(self, jira):
        jira.update_sprint(5, "active")
        args, kwargs = jira.put.call_args
        assert args[0] == "https://fake_url/rest/agile/1.0/sprint/5"
        assert kwargs["json"]["state"] == "active"

    def test_update_sprint_invalid_state_raises(self, jira):
        with pytest.raises(ValueError):
            jira.update_sprint(5, "invalid")

    # ------------------------------------------------------------------ #
    # Projects                                                             #
    # ------------------------------------------------------------------ #

    def test_get_project(self, jira):
        jira.get_project("PROJ")
        jira.get.assert_called_with("/rest/api/2/project/PROJ")

    def test_list_projects(self, jira):
        jira.list_projects()
        jira.get.assert_called_with("/rest/api/2/project")

    def test_create_project(self, jira):
        jira.create_project("NEWP", "New Project", "software")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/project"
        assert kwargs["json"]["key"] == "NEWP"
        assert kwargs["json"]["projectTypeKey"] == "software"

    def test_delete_project(self, jira):
        jira.delete_project("OLDP")
        jira.delete.assert_called_with("/rest/api/2/project/OLDP")

    # ------------------------------------------------------------------ #
    # Attachments                                                          #
    # ------------------------------------------------------------------ #

    def test_add_attachment(self, jira):
        jira.upload = MagicMock(return_value=[{"id": "1"}])
        jira.add_attachment("TEST-1", "/tmp/file.txt")
        jira.upload.assert_called_with(
            "/rest/api/2/issue/TEST-1/attachments",
            "/tmp/file.txt",
            "application/octet-stream",
        )

    def test_get_attachments(self, jira):
        jira.get_attachments("TEST-1")
        jira.get.assert_called_with("/rest/api/2/issue/TEST-1?fields=attachment")

    def test_delete_attachment(self, jira):
        jira.delete_attachment("att-123")
        jira.delete.assert_called_with("/rest/api/2/attachment/att-123")

    # ------------------------------------------------------------------ #
    # Worklogs                                                             #
    # ------------------------------------------------------------------ #

    def test_add_worklog(self, jira):
        jira.add_worklog("TEST-1", "2h")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/issue/TEST-1/worklog"
        assert kwargs["json"]["timeSpent"] == "2h"

    def test_get_worklogs(self, jira):
        jira.get_worklogs("TEST-1")
        jira.get.assert_called_with("/rest/api/2/issue/TEST-1/worklog")

    def test_delete_worklog(self, jira):
        jira.delete_worklog("TEST-1", "wl-99")
        jira.delete.assert_called_with("/rest/api/2/issue/TEST-1/worklog/wl-99")

    # ------------------------------------------------------------------ #
    # Versions                                                             #
    # ------------------------------------------------------------------ #

    def test_get_versions(self, jira):
        jira.get_versions("PROJ")
        jira.get.assert_called_with("/rest/api/2/project/PROJ/versions")

    def test_create_version(self, jira):
        jira.create_version("PROJ", "1.0.0")
        args, kwargs = jira.post.call_args
        assert args[0] == "/rest/api/2/version"
        assert kwargs["json"]["name"] == "1.0.0"
        assert kwargs["json"]["project"] == "PROJ"

    def test_update_version(self, jira):
        jira.update_version("v-1", name="1.0.1", released=True)
        args, kwargs = jira.put.call_args
        assert args[0] == "/rest/api/2/version/v-1"
        assert kwargs["json"]["name"] == "1.0.1"
        assert kwargs["json"]["released"] is True

    def test_delete_version(self, jira):
        jira.delete_version("v-1")
        jira.delete.assert_called_with("/rest/api/2/version/v-1")

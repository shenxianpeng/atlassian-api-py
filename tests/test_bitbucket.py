import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from atlassian.bitbucket import Bitbucket


class TestBitbucket:
    @pytest.fixture
    def bitbucket(self):
        bb = Bitbucket(url="https://fake_url")
        # stub HTTP verbs
        bb.get = MagicMock()
        bb.put = MagicMock()
        bb.post = MagicMock()
        bb.delete = MagicMock()
        return bb

    def test_get_paged_simple(self, bitbucket):
        # Mock response for _get_paged
        mock_response = SimpleNamespace(
            values=[{"key": "val1"}, {"key": "val2"}], isLastPage=True
        )
        bitbucket.get = MagicMock(return_value=mock_response)

        result = bitbucket._get_paged("/test/url", {})
        assert len(result) == 2
        assert result[0]["key"] == "val1"

    def test_get_paged_no_values(self, bitbucket):
        mock_response = SimpleNamespace(values=None, isLastPage=True)
        bitbucket.get = MagicMock(return_value=mock_response)

        result = bitbucket._get_paged("/test/url", {})
        assert result == []

    def test_get_paged_with_pagination(self, bitbucket):
        responses = [
            SimpleNamespace(
                values=[{"key": "val1"}], isLastPage=False, nextPageStart=1
            ),
            SimpleNamespace(values=[{"key": "val2"}], isLastPage=True),
        ]
        bitbucket.get = MagicMock(side_effect=responses)

        result = bitbucket._get_paged("/test/url", {})
        assert len(result) == 2

    def test_get_paged_with_limit(self, bitbucket):
        responses = [
            SimpleNamespace(
                values=[{"key": "val1"}], isLastPage=False, nextPageStart=1
            ),
            SimpleNamespace(values=[{"key": "val2"}], isLastPage=True),
        ]
        bitbucket.get = MagicMock(side_effect=responses)

        result = bitbucket._get_paged("/test/url", {"limit": 5})
        assert len(result) == 2

    def test_get_paged_limit_exceeded(self, bitbucket):
        # Test when limit is exceeded during pagination
        responses = [
            SimpleNamespace(
                values=[{"key": f"val{i}"} for i in range(3)],
                isLastPage=False,
                nextPageStart=3,
            ),
            SimpleNamespace(values=[{"key": "val4"}], isLastPage=True),
        ]
        bitbucket.get = MagicMock(side_effect=responses)

        # Request only 2 items
        result = bitbucket._get_paged("/test/url", {"limit": 2})
        # Should stop when limit would go negative
        assert len(result) == 3

    def test_get_paged_none_response(self, bitbucket):
        """Test that _get_paged returns empty list when get() returns None."""
        bitbucket.get = MagicMock(return_value=None)
        result = bitbucket._get_paged("/test/url", {})
        assert result == []

    def test_get_paged_string_response(self, bitbucket):
        """Test that _get_paged returns empty list when response is a string (JSON parse failure)."""
        bitbucket.get = MagicMock(return_value="error message")
        result = bitbucket._get_paged("/test/url", {})
        assert result == []

    def test_get_paged_no_values_attribute(self, bitbucket):
        """Test that _get_paged returns empty list when response lacks values attribute."""
        mock_response = SimpleNamespace(isLastPage=True)
        bitbucket.get = MagicMock(return_value=mock_response)
        result = bitbucket._get_paged("/test/url", {})
        assert result == []

    def test_get_project_repo(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_project_repo("PROJ")
        bitbucket._get_paged.assert_called_once()

    def test_get_project_repo_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_project_repo("PROJ", start=10, limit=50)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 10
        assert kwargs["params"]["limit"] == 50

    def test_get_project_repo_name(self, bitbucket):
        mock_repos = [SimpleNamespace(name="repo1"), SimpleNamespace(name="repo2")]
        bitbucket.get_project_repo = MagicMock(return_value=mock_repos)

        result = bitbucket.get_project_repo_name("PROJ")
        assert result == ["repo1", "repo2"]

    def test_get_repo_info(self, bitbucket):
        bitbucket.get_repo_info("PROJ", "my-repo")
        bitbucket.get.assert_called_with("/rest/api/latest/projects/PROJ/repos/my-repo")

    def test_get_repo_branch(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_repo_branch("PROJ", "repo")
        bitbucket._get_paged.assert_called_once()

    def test_get_repo_branch_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_repo_branch("PROJ", "repo", start=5, limit=100)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 100

    def test_create_branch(self, bitbucket):
        bitbucket.create_branch("PROJ", "repo", "feature-branch", "master")
        args, kwargs = bitbucket.post.call_args
        assert "/branch-utils/1.0/" in args[0]
        assert kwargs["json"]["name"] == "feature-branch"
        assert kwargs["json"]["startPoint"] == "master"

    def test_delete_branch(self, bitbucket):
        bitbucket.delete_branch("PROJ", "repo", "old-branch", "commit123")
        args, kwargs = bitbucket.delete.call_args
        assert "/branch-utils/latest/" in args[0]
        assert kwargs["json"]["name"] == "old-branch"
        assert kwargs["json"]["endPoint"] == "commit123"

    def test_get_merged_branch(self, bitbucket):
        mock_branch = SimpleNamespace(
            displayId="feature-1",
            metadata=SimpleNamespace(
                **{
                    "com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata": SimpleNamespace(
                        pullRequest=SimpleNamespace(state="MERGED"), merged=True
                    )
                }
            ),
        )
        bitbucket._get_paged = MagicMock(return_value=[mock_branch])

        result = bitbucket.get_merged_branch("PROJ", "repo")
        assert "feature-1" in result

    def test_get_merged_branch_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_merged_branch("PROJ", "repo", start=10, limit=50)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 10
        assert kwargs["params"]["limit"] == 50

    def test_get_merged_branch_no_pr_metadata(self, bitbucket):
        mock_branch = SimpleNamespace(displayId="feature-2", metadata=SimpleNamespace())
        bitbucket._get_paged = MagicMock(return_value=[mock_branch])

        result = bitbucket.get_merged_branch("PROJ", "repo")
        assert result == []

    def test_get_merged_branch_no_state(self, bitbucket):
        mock_branch = SimpleNamespace(
            displayId="feature-3",
            metadata=SimpleNamespace(
                **{
                    "com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata": SimpleNamespace(
                        merged=True
                    )
                }
            ),
        )
        bitbucket._get_paged = MagicMock(return_value=[mock_branch])

        result = bitbucket.get_merged_branch("PROJ", "repo")
        assert "feature-3" in result

    def test_get_merged_branch_no_merged_attr(self, bitbucket):
        mock_branch = SimpleNamespace(
            displayId="feature-4",
            metadata=SimpleNamespace(
                **{
                    "com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata": SimpleNamespace(
                        pullRequest=SimpleNamespace(state="MERGED")
                    )
                }
            ),
        )
        bitbucket._get_paged = MagicMock(return_value=[mock_branch])

        result = bitbucket.get_merged_branch("PROJ", "repo")
        assert "feature-4" in result

    def test_get_branch_commits(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_branch_commits("PROJ", "repo", "master")
        bitbucket._get_paged.assert_called_once()

    def test_get_branch_commits_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_branch_commits("PROJ", "repo", "master", start=5, limit=100)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 100

    def test_get_pull_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request("PROJ", "repo")
        bitbucket._get_paged.assert_called_once()

    def test_get_pull_request_with_state(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request("PROJ", "repo", pr_state="OPEN")
        args, kwargs = bitbucket._get_paged.call_args
        assert "state=OPEN" in args[0]

    def test_get_pull_request_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request("PROJ", "repo", start=5, limit=100)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 100

    def test_get_pull_request_destination_branch_name(self, bitbucket):
        mock_pr = SimpleNamespace(id=123, toRef=SimpleNamespace(displayId="master"))
        bitbucket.get_pull_request = MagicMock(return_value=[mock_pr])

        result = bitbucket.get_pull_request_destination_branch_name("PROJ", "repo", 123)
        assert result == "master"

    def test_get_pull_request_source_branch_name(self, bitbucket):
        mock_pr = SimpleNamespace(id=456, fromRef=SimpleNamespace(displayId="feature"))
        bitbucket.get_pull_request = MagicMock(return_value=[mock_pr])

        result = bitbucket.get_pull_request_source_branch_name("PROJ", "repo", 456)
        assert result == "feature"

    def test_get_pull_request_jira_key(self, bitbucket):
        bitbucket.get_pull_request_source_branch_name = MagicMock(
            return_value="feature/TEST-123-description"
        )

        result = bitbucket.get_pull_request_jira_key("PROJ", "repo", 789)
        assert result == "TEST-123"

    def test_get_pull_request_jira_key_no_match(self, bitbucket):
        bitbucket.get_pull_request_source_branch_name = MagicMock(
            return_value="feature-branch"
        )

        result = bitbucket.get_pull_request_jira_key("PROJ", "repo", 789)
        assert result is None

    def test_get_pull_request_jira_key_branch_not_found(self, bitbucket):
        bitbucket.get_pull_request_source_branch_name = MagicMock(return_value=None)
        result = bitbucket.get_pull_request_jira_key("PROJ", "repo", 123)
        assert result is None

    def test_get_pull_request_id(self, bitbucket):
        mock_prs = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        bitbucket.get_pull_request = MagicMock(return_value=mock_prs)

        result = bitbucket.get_pull_request_id("PROJ", "repo")
        assert result == [1, 2]

    def test_get_pull_request_overview(self, bitbucket):
        bitbucket.get_pull_request_overview("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123"
        )

    def test_get_pull_request_diff(self, bitbucket):
        bitbucket.get_pull_request_diff("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123/diff"
        )

    def test_get_pull_request_raw_diff(self, bitbucket):
        bitbucket.get_pull_request_raw_diff("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123.diff"
        )

    def test_get_pull_request_patch(self, bitbucket):
        bitbucket.get_pull_request_patch("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123.patch"
        )

    def test_get_pull_request_commits(self, bitbucket):
        bitbucket.get_pull_request_commits("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123/commits"
        )

    def test_get_pull_request_activities(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request_activities("PROJ", "repo", 123)
        bitbucket._get_paged.assert_called_once()

    def test_get_pull_request_activities_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request_activities("PROJ", "repo", 123, start=5, limit=100)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 100

    def test_get_pull_request_merge(self, bitbucket):
        bitbucket.get_pull_request_merge("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123/merge"
        )

    def test_get_branch_committer_info(self, bitbucket):
        mock_commits = [
            SimpleNamespace(committer="user1"),
            SimpleNamespace(committer="user2"),
        ]
        bitbucket.get_branch_commits = MagicMock(return_value=mock_commits)

        result = bitbucket.get_branch_committer_info("PROJ", "repo", "master")
        assert result == ["user1", "user2"]

    def test_get_pull_request_comments(self, bitbucket):
        bitbucket.get_pull_request_comments("PROJ", "repo", 123)
        bitbucket.get.assert_called_with(
            "/rest/ui/latest/projects/PROJ/repos/repo/pull-requests/123/comments"
        )

    def test_add_pull_request_comment(self, bitbucket):
        bitbucket.add_pull_request_comment("PROJ", "repo", 123, "Great work!")
        args, kwargs = bitbucket.post.call_args
        assert "/comments" in args[0]
        assert kwargs["json"]["text"] == "Great work!"

    def test_add_pull_request_inline_comment(self, bitbucket):
        bitbucket.add_pull_request_inline_comment(
            "PROJ", "repo", 123, "Needs fix", "src/main.py", 42
        )
        args, kwargs = bitbucket.post.call_args
        assert (
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123/comments"
            == args[0]
        )
        assert kwargs["json"]["text"] == "Needs fix"
        anchor = kwargs["json"]["anchor"]
        assert anchor["line"] == 42
        assert anchor["lineType"] == "CONTEXT"
        assert anchor["fileType"] == "TO"
        assert anchor["path"] == "src/main.py"
        assert "srcPath" not in anchor

    def test_add_pull_request_inline_comment_custom_line_type(self, bitbucket):
        bitbucket.add_pull_request_inline_comment(
            "PROJ",
            "repo",
            123,
            "Added line",
            "src/main.py",
            10,
            line_type="ADDED",
            file_type="TO",
        )
        args, kwargs = bitbucket.post.call_args
        anchor = kwargs["json"]["anchor"]
        assert anchor["lineType"] == "ADDED"
        assert anchor["fileType"] == "TO"

    def test_add_pull_request_inline_comment_with_src_path(self, bitbucket):
        bitbucket.add_pull_request_inline_comment(
            "PROJ",
            "repo",
            123,
            "Rename check",
            "new/path.py",
            5,
            src_path="old/path.py",
        )
        args, kwargs = bitbucket.post.call_args
        anchor = kwargs["json"]["anchor"]
        assert anchor["path"] == "new/path.py"
        assert anchor["srcPath"] == "old/path.py"

    def test_update_pull_request_comment(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Old comment text",
                id=999,
                version=1,
                severity="NORMAL",
                state="OPEN",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.update_pull_request_comment(
            "PROJ", "repo", 123, "Old comment", "New comment"
        )
        args, kwargs = bitbucket.put.call_args
        assert "/comments/999" in args[0]
        assert kwargs["json"]["text"] == "New comment"

    def test_update_pull_request_comment_exact_match(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Exact match comment",
                id=777,
                version=3,
                severity="BLOCKER",
                state="RESOLVED",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.update_pull_request_comment(
            "PROJ", "repo", 123, "Exact match", "Updated"
        )
        args, kwargs = bitbucket.put.call_args
        assert kwargs["json"]["severity"] == "BLOCKER"
        assert kwargs["json"]["state"] == "RESOLVED"

    def test_update_pull_request_comment_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.update_pull_request_comment(
            "PROJ", "repo", 123, "Missing", "New"
        )
        assert result is None

    def test_update_pull_request_comment_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.update_pull_request_comment(
            "PROJ", "repo", 123, "Old", "New"
        )
        assert result is None

    def test_delete_pull_request_comment(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(text="Delete me", id=888, version=2)
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.delete_pull_request_comment("PROJ", "repo", 123, "Delete me")
        args, kwargs = bitbucket.delete.call_args
        assert "/comments/888" in args[0]
        assert "version=2" in args[0]

    def test_delete_pull_request_comment_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.delete_pull_request_comment("PROJ", "repo", 123, "Missing")
        assert result is None

    def test_delete_pull_request_comment_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="MERGED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.delete_pull_request_comment("PROJ", "repo", 123, "Text")
        assert result is None

    def test_find_comment_in_activities_found(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="some comment text",
                id=42,
                version=2,
                severity="BLOCKER",
                state="OPEN",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket._find_comment_in_activities(
            "PROJ", "repo", 1, "some comment"
        )
        assert result is not None
        assert result["id"] == 42
        assert result["version"] == 2
        assert result["text"] == "some comment text"
        assert result["severity"] == "BLOCKER"
        assert result["state"] == "OPEN"

    def test_find_comment_in_activities_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket._find_comment_in_activities("PROJ", "repo", 1, "missing")
        assert result is None

    def test_find_comment_in_activities_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket._find_comment_in_activities("PROJ", "repo", 1, "text")
        assert result is None

    def test_resolve_pull_request_comment(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Fix this bug", id=101, version=1, severity="BLOCKER", state="OPEN"
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.resolve_pull_request_comment("PROJ", "repo", 123, "Fix this bug")
        args, kwargs = bitbucket.put.call_args
        assert "/comments/101" in args[0]
        assert kwargs["json"]["state"] == "RESOLVED"
        assert kwargs["json"]["severity"] == "BLOCKER"

    def test_resolve_pull_request_comment_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.resolve_pull_request_comment("PROJ", "repo", 123, "Missing")
        assert result is None

    def test_resolve_pull_request_comment_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.resolve_pull_request_comment("PROJ", "repo", 123, "Text")
        assert result is None

    def test_reopen_pull_request_comment(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Fix this bug",
                id=102,
                version=2,
                severity="BLOCKER",
                state="RESOLVED",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.reopen_pull_request_comment("PROJ", "repo", 123, "Fix this bug")
        args, kwargs = bitbucket.put.call_args
        assert "/comments/102" in args[0]
        assert kwargs["json"]["state"] == "OPEN"
        assert kwargs["json"]["severity"] == "BLOCKER"

    def test_reopen_pull_request_comment_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.reopen_pull_request_comment("PROJ", "repo", 123, "Missing")
        assert result is None

    def test_reopen_pull_request_comment_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.reopen_pull_request_comment("PROJ", "repo", 123, "Text")
        assert result is None

    def test_convert_comment_to_task(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Please fix this",
                id=201,
                version=1,
                severity="NORMAL",
                state="OPEN",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.convert_comment_to_task("PROJ", "repo", 123, "Please fix this")
        args, kwargs = bitbucket.put.call_args
        assert "/comments/201" in args[0]
        assert kwargs["json"]["severity"] == "BLOCKER"
        assert kwargs["json"]["state"] == "OPEN"

    def test_convert_comment_to_task_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.convert_comment_to_task("PROJ", "repo", 123, "Missing")
        assert result is None

    def test_convert_comment_to_task_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.convert_comment_to_task("PROJ", "repo", 123, "Text")
        assert result is None

    def test_convert_task_to_comment(self, bitbucket):
        mock_activity = SimpleNamespace(
            comment=SimpleNamespace(
                text="Task to fix",
                id=301,
                version=3,
                severity="BLOCKER",
                state="OPEN",
            )
        )
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        bitbucket.convert_task_to_comment("PROJ", "repo", 123, "Task to fix")
        args, kwargs = bitbucket.put.call_args
        assert "/comments/301" in args[0]
        assert kwargs["json"]["severity"] == "NORMAL"
        assert kwargs["json"]["state"] == "OPEN"

    def test_convert_task_to_comment_not_found(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(return_value=[])

        result = bitbucket.convert_task_to_comment("PROJ", "repo", 123, "Missing")
        assert result is None

    def test_convert_task_to_comment_no_comment_attr(self, bitbucket):
        mock_activity = SimpleNamespace(action="OPENED")
        bitbucket.get_pull_request_activities = MagicMock(return_value=[mock_activity])

        result = bitbucket.convert_task_to_comment("PROJ", "repo", 123, "Text")
        assert result is None

    def test_get_file_change_history(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_file_change_history("PROJ", "repo", "master", "src/file.py")
        bitbucket._get_paged.assert_called_once()

    def test_get_file_change_history_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_file_change_history(
            "PROJ", "repo", "master", "src/file.py", start=5, limit=100
        )
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 100

    def test_get_file_content(self, bitbucket):
        bitbucket.get_file_content("PROJ", "repo", "master", "README.md")
        bitbucket.get.assert_called_with(
            "/projects/PROJ/repos/repo/raw/README.md?at=master"
        )

    def test_get_build_status(self, bitbucket):
        bitbucket.get_build_status("abc123")
        bitbucket.get.assert_called_with("/rest/build-status/latest/commits/abc123")

    def test_update_build_status(self, bitbucket):
        bitbucket.update_build_status(
            "commit123",
            "SUCCESSFUL",
            "build-key",
            "Build Name",
            "https://build.url",
            "Build passed",
        )
        args, kwargs = bitbucket.post.call_args
        assert "/build-status/latest/" in args[0]
        assert kwargs["json"]["state"] == "SUCCESSFUL"

    def test_get_user(self, bitbucket):
        bitbucket.get_user("jsmith")
        bitbucket.get.assert_called_with("/rest/api/latest/users/jsmith")

    def test_review_pull_request(self, bitbucket):
        bitbucket.review_pull_request("PROJ", "repo", 123, "jsmith", "APPROVED")
        args, kwargs = bitbucket.put.call_args
        assert "/participants/jsmith" in args[0]
        assert kwargs["json"]["status"] == "APPROVED"

    def test_review_pull_request_default_status(self, bitbucket):
        bitbucket.review_pull_request("PROJ", "repo", 123, "jsmith")
        args, kwargs = bitbucket.put.call_args
        assert kwargs["json"]["status"] == "APPROVED"

    def test_update_pull_request_description(self, bitbucket):
        mock_pr = SimpleNamespace(version=5)
        bitbucket.get_pull_request_overview = MagicMock(return_value=mock_pr)

        bitbucket.update_pull_request_description(
            "PROJ",
            "repo",
            123,
            "New description here",
        )
        args, kwargs = bitbucket.put.call_args
        assert args[0] == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123"
        assert "description" in kwargs["json"]
        assert kwargs["json"]["description"] == "New description here"
        assert kwargs["json"]["version"] == 5

    def test_update_pull_request_title(self, bitbucket):
        mock_pr = SimpleNamespace(version=3)
        bitbucket.get_pull_request_overview = MagicMock(return_value=mock_pr)

        bitbucket.update_pull_request_title(
            "PROJ",
            "repo",
            456,
            "New concise title",
        )
        args, kwargs = bitbucket.put.call_args
        assert args[0] == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/456"
        assert "title" in kwargs["json"]
        assert kwargs["json"]["title"] == "New concise title"
        assert kwargs["json"]["version"] == 3

    def test_update_pull_request_reviewers(self, bitbucket):
        mock_pr = SimpleNamespace(version=2)
        bitbucket.get_pull_request_overview = MagicMock(return_value=mock_pr)

        reviewers = ["alice", "bob"]
        bitbucket.update_pull_request_reviewers(
            "PROJ",
            "repo",
            789,
            reviewers,
        )
        args, kwargs = bitbucket.put.call_args
        assert args[0] == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/789"
        assert "reviewers" in kwargs["json"]
        assert kwargs["json"]["reviewers"] == reviewers
        assert kwargs["json"]["version"] == 2

    def test_update_pull_request_destination(self, bitbucket):
        mock_pr = SimpleNamespace(version=1)
        bitbucket.get_pull_request_overview = MagicMock(return_value=mock_pr)

        bitbucket.update_pull_request_destination(
            "PROJ",
            "repo",
            987,
            "release/1.2.3",
        )
        args, kwargs = bitbucket.put.call_args
        assert args[0] == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/987"
        assert "destination" in kwargs["json"]
        assert kwargs["json"]["destination"]["branch"]["name"] == "release/1.2.3"
        assert kwargs["json"]["version"] == 1

    def test_create_pull_request(self, bitbucket):
        bitbucket.create_pull_request("PROJ", "repo", "My PR", "feature/branch", "main")
        args, kwargs = bitbucket.post.call_args
        assert args[0] == "/rest/api/latest/projects/PROJ/repos/repo/pull-requests"
        assert kwargs["json"]["title"] == "My PR"
        assert kwargs["json"]["fromRef"]["id"] == "refs/heads/feature/branch"
        assert kwargs["json"]["toRef"]["id"] == "refs/heads/main"
        assert "description" not in kwargs["json"]
        assert "reviewers" not in kwargs["json"]

    def test_create_pull_request_with_optional_fields(self, bitbucket):
        bitbucket.create_pull_request(
            "PROJ",
            "repo",
            "My PR",
            "feature/branch",
            "main",
            description="PR description",
            reviewers=["alice", "bob"],
        )
        args, kwargs = bitbucket.post.call_args
        assert kwargs["json"]["description"] == "PR description"
        assert kwargs["json"]["reviewers"] == [
            {"user": {"slug": "alice"}},
            {"user": {"slug": "bob"}},
        ]

    def test_merge_pull_request(self, bitbucket):
        bitbucket.merge_pull_request("PROJ", "repo", 123, 3)
        args, kwargs = bitbucket.post.call_args
        assert (
            args[0]
            == "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/123/merge"
        )
        assert kwargs["params"]["version"] == 3

    def test_decline_pull_request(self, bitbucket):
        bitbucket.decline_pull_request("PROJ", "repo", 456, 1)
        args, kwargs = bitbucket.post.call_args
        assert (
            args[0]
            == "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/456/decline"
        )
        assert kwargs["params"]["version"] == 1

    def test_get_tags(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_tags("PROJ", "repo")
        bitbucket._get_paged.assert_called_once()
        args, kwargs = bitbucket._get_paged.call_args
        assert args[0] == "/rest/api/latest/projects/PROJ/repos/repo/tags"

    def test_get_tags_with_params(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_tags("PROJ", "repo", start=5, limit=10)
        args, kwargs = bitbucket._get_paged.call_args
        assert kwargs["params"]["start"] == 5
        assert kwargs["params"]["limit"] == 10

    def test_create_tag(self, bitbucket):
        bitbucket.create_tag("PROJ", "repo", "v1.0.0", "abc123")
        args, kwargs = bitbucket.post.call_args
        assert args[0] == "/rest/api/latest/projects/PROJ/repos/repo/tags"
        assert kwargs["json"]["name"] == "v1.0.0"
        assert kwargs["json"]["startPoint"] == "abc123"
        assert "message" not in kwargs["json"]

    def test_create_tag_with_message(self, bitbucket):
        bitbucket.create_tag("PROJ", "repo", "v2.0.0", "def456", message="Release 2.0")
        args, kwargs = bitbucket.post.call_args
        assert kwargs["json"]["message"] == "Release 2.0"

    @staticmethod
    def _serve_pages(pages):
        """Fake ``get`` that serves ``pages`` and snapshots each call's params."""
        calls = []

        def fake_get(url, params=None):
            calls.append((url, dict(params or {})))
            return pages[len(calls) - 1]

        return fake_get, calls

    def test_get_paged_requests_next_page_start(self, bitbucket):
        fake_get, calls = self._serve_pages(
            [
                SimpleNamespace(values=[1, 2], isLastPage=False, nextPageStart=2),
                SimpleNamespace(values=[3], isLastPage=True),
            ]
        )
        bitbucket.get = fake_get

        result = bitbucket._get_paged("/test/url", {"limit": 10})

        assert result == [1, 2, 3]
        assert calls == [
            ("/test/url", {"limit": 10}),
            ("/test/url", {"limit": 8, "start": 2}),
        ]

    def test_get_paged_stops_when_next_page_is_not_json(self, bitbucket):
        fake_get, calls = self._serve_pages(
            [
                SimpleNamespace(values=[1], isLastPage=False, nextPageStart=1),
                "<html>proxy error</html>",
            ]
        )
        bitbucket.get = fake_get

        assert bitbucket._get_paged("/test/url", {}) == [1]
        assert len(calls) == 2

    def test_get_paged_tolerates_empty_next_page(self, bitbucket):
        fake_get, _ = self._serve_pages(
            [
                SimpleNamespace(values=[1], isLastPage=False, nextPageStart=1),
                SimpleNamespace(values=None, isLastPage=True),
            ]
        )
        bitbucket.get = fake_get

        assert bitbucket._get_paged("/test/url", {}) == [1]

    def test_get_merged_branch_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_merged_branch("PROJ", "repo")
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/branches"
            "?base=refs/heads/master&details=true",
            params={},
        )

    def test_get_merged_branch_skips_open_pull_request(self, bitbucket):
        metadata_key = "com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata"
        open_branch = SimpleNamespace(
            displayId="feature-open",
            metadata=SimpleNamespace(
                **{
                    metadata_key: SimpleNamespace(
                        pullRequest=SimpleNamespace(state="OPEN"), merged=False
                    )
                }
            ),
        )
        bitbucket._get_paged = MagicMock(return_value=[open_branch])

        assert bitbucket.get_merged_branch("PROJ", "repo") == []

    @pytest.mark.parametrize(
        "method, ref",
        [
            ("get_pull_request_destination_branch_name", "toRef"),
            ("get_pull_request_source_branch_name", "fromRef"),
        ],
    )
    def test_pull_request_branch_name_without_pull_requests(
        self, bitbucket, method, ref
    ):
        bitbucket.get_pull_request = MagicMock(return_value=[])

        assert getattr(bitbucket, method)("PROJ", "repo", 1) is None
        bitbucket.get_pull_request.assert_called_once_with("PROJ", "repo", limit=25)

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("get_pull_request_destination_branch_name", "main"),
            ("get_pull_request_source_branch_name", "feature/TEST-1"),
        ],
    )
    def test_pull_request_branch_name_found_on_second_attempt(
        self, bitbucket, method, expected
    ):
        others = [SimpleNamespace(id=i) for i in range(25)]
        target = SimpleNamespace(
            id=99,
            toRef=SimpleNamespace(displayId="main"),
            fromRef=SimpleNamespace(displayId="feature/TEST-1"),
        )
        bitbucket.get_pull_request = MagicMock(side_effect=[others, others + [target]])

        # The ID may be given as a string; it is compared as an integer.
        assert getattr(bitbucket, method)("PROJ", "repo", "99") == expected
        limits = [c.kwargs["limit"] for c in bitbucket.get_pull_request.call_args_list]
        assert limits == [25, 50]

    @pytest.mark.parametrize(
        "method",
        [
            "get_pull_request_destination_branch_name",
            "get_pull_request_source_branch_name",
        ],
    )
    def test_pull_request_branch_name_gives_up_after_max_attempts(
        self, bitbucket, method
    ):
        def full_page(project_key, repo_slug, limit):
            return [SimpleNamespace(id=-1)] * limit

        bitbucket.get_pull_request = MagicMock(side_effect=full_page)

        assert getattr(bitbucket, method)("PROJ", "repo", 1) is None
        assert bitbucket.get_pull_request.call_count == 100

    def test_get_pull_request_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=["pr"])
        assert bitbucket.get_pull_request("PROJ", "repo") == ["pr"]
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests?state=ALL",
            params={},
        )

    def test_get_pull_request_id_passes_filters(self, bitbucket):
        bitbucket.get_pull_request = MagicMock(return_value=[])
        bitbucket.get_pull_request_id("PROJ", "repo", "MERGED", start=5, limit=10)
        bitbucket.get_pull_request.assert_called_once_with(
            "PROJ", "repo", pr_state="MERGED", start=5, limit=10
        )

    def test_get_project_repo_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_project_repo("PROJ")
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/", params={}
        )

    def test_get_repo_branch_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_repo_branch("PROJ", "repo")
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/branches", params={}
        )

    def test_get_branch_commits_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_branch_commits("PROJ", "repo", "master")
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/commits/?until=master",
            params={},
        )

    def test_get_pull_request_activities_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_pull_request_activities("PROJ", "repo", 7)
        bitbucket._get_paged.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/7/activities",
            params={},
        )

    def test_get_branch_committer_info_passes_paging(self, bitbucket):
        bitbucket.get_branch_commits = MagicMock(return_value=[])
        assert bitbucket.get_branch_committer_info("P", "r", "main", 5, 10) == []
        bitbucket.get_branch_commits.assert_called_once_with(
            "P", "r", "main", start=5, limit=10
        )

    def test_create_and_delete_branch_requests(self, bitbucket):
        bitbucket.create_branch("PROJ", "repo", "feature-x", "main")
        bitbucket.post.assert_called_once_with(
            "/rest/branch-utils/1.0/projects/PROJ/repos/repo/branches",
            json={"name": "feature-x", "startPoint": "main"},
        )
        bitbucket.delete_branch("PROJ", "repo", "feature-x", "abc123")
        bitbucket.delete.assert_called_once_with(
            "/rest/branch-utils/latest/projects/PROJ/repos/repo/branches",
            json={"name": "feature-x", "endPoint": "abc123"},
        )

    @staticmethod
    def _activity(text, comment_id, version=1, severity="NORMAL", state="OPEN"):
        return SimpleNamespace(
            comment=SimpleNamespace(
                text=text,
                id=comment_id,
                version=version,
                severity=severity,
                state=state,
            )
        )

    def test_update_pull_request_comment_skips_other_comments(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(
            return_value=[
                SimpleNamespace(action="OPENED"),
                self._activity("unrelated", 1),
                self._activity("the old text here", 2, version=4),
            ]
        )

        bitbucket.update_pull_request_comment("PROJ", "repo", 9, "old text", "new")

        bitbucket.put.assert_called_once_with(
            "/rest/api/latest/projects/PROJ/repos/repo/pull-requests/9/comments/2",
            json={"version": 4, "text": "new", "severity": "NORMAL", "state": "OPEN"},
        )

    def test_delete_pull_request_comment_requires_exact_text(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(
            return_value=[
                self._activity("Delete me too", 1),
                self._activity("Delete me", 2, version=3),
            ]
        )

        bitbucket.delete_pull_request_comment("PROJ", "repo", 9, "Delete me")

        args, kwargs = bitbucket.delete.call_args
        assert args[0].startswith(
            "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/9/comments/2"
        )
        assert args[0].endswith("version=3")

    def test_find_comment_in_activities_skips_other_comments(self, bitbucket):
        bitbucket.get_pull_request_activities = MagicMock(
            return_value=[self._activity("first", 1), self._activity("second", 2)]
        )

        found = bitbucket._find_comment_in_activities("PROJ", "repo", 9, "second")

        assert found == {
            "id": 2,
            "version": 1,
            "text": "second",
            "severity": "NORMAL",
            "state": "OPEN",
        }

    @pytest.mark.parametrize(
        "method, value",
        [
            ("update_pull_request_description", "description"),
            ("update_pull_request_title", "title"),
            ("update_pull_request_reviewers", [{"user": {"name": "alice"}}]),
            ("update_pull_request_destination", "main"),
        ],
    )
    @pytest.mark.parametrize("overview", [None, "<html>not json</html>"])
    def test_update_pull_request_needs_overview(
        self, bitbucket, method, value, overview
    ):
        bitbucket.get_pull_request_overview = MagicMock(return_value=overview)

        assert getattr(bitbucket, method)("PROJ", "repo", 1, value) is None
        bitbucket.put.assert_not_called()

    def test_get_file_change_history_request(self, bitbucket):
        bitbucket._get_paged = MagicMock(return_value=[])
        bitbucket.get_file_change_history("PROJ", "repo", "main", "src/a.py")
        url = bitbucket._get_paged.call_args.args[0]
        assert url.startswith("/rest/api/latest/projects/PROJ/repos/repo/commits?")
        assert "path=src/a.py" in url
        assert "until=refs%2Fheads%2Fmain" in url

    def test_update_build_status_payload(self, bitbucket):
        bitbucket.update_build_status(
            "abc123", "FAILED", "ci", "CI build", "https://ci.example.com/1"
        )
        bitbucket.post.assert_called_once_with(
            "/rest/build-status/latest/commits/abc123",
            json={
                "state": "FAILED",
                "key": "ci",
                "name": "CI build",
                "url": "https://ci.example.com/1",
                "description": "ManuallyCheckBuildPass",
            },
        )

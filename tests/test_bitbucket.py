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

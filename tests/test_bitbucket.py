import pytest
from unittest.mock import MagicMock
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

    def test_update_pull_request_description(self, bitbucket):
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

    def test_update_pull_request_title(self, bitbucket):
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

    def test_update_pull_request_reviewers(self, bitbucket):
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

    def test_update_pull_request_destination(self, bitbucket):
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

    def test_resolve_blocker_comment(self, bitbucket):
        bitbucket.resolve_blocker_comment(
            "PROJ",
            "repo",
            123,
            456,
        )
        args, kwargs = bitbucket.put.call_args
        assert (
            args[0]
            == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123/blocker-comments/456"
        )
        assert "state" in kwargs["json"]
        assert kwargs["json"]["state"] == "RESOLVED"

    def test_reopen_blocker_comment(self, bitbucket):
        bitbucket.reopen_blocker_comment(
            "PROJ",
            "repo",
            123,
            456,
        )
        args, kwargs = bitbucket.put.call_args
        assert (
            args[0]
            == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123/blocker-comments/456"
        )
        assert "state" in kwargs["json"]
        assert kwargs["json"]["state"] == "OPEN"

    def test_convert_task_to_comment(self, bitbucket):
        bitbucket.convert_task_to_comment(
            "PROJ",
            "repo",
            123,
            456,
        )
        args, kwargs = bitbucket.put.call_args
        assert (
            args[0]
            == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123/blocker-comments/456"
        )
        assert "severity" in kwargs["json"]
        assert kwargs["json"]["severity"] == "NORMAL"

    def test_convert_comment_to_task(self, bitbucket):
        bitbucket.convert_comment_to_task(
            "PROJ",
            "repo",
            123,
            456,
        )
        args, kwargs = bitbucket.put.call_args
        assert (
            args[0]
            == "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123/blocker-comments/456"
        )
        assert "severity" in kwargs["json"]
        assert kwargs["json"]["severity"] == "BLOCKER"

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
        bitbucket.put.assert_called_with(
            "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/123",
            json={"description": "New description here"},
        )

    def test_update_pull_request_title(self, bitbucket):
        bitbucket.update_pull_request_title(
            "PROJ",
            "repo",
            456,
            "New concise title",
        )
        bitbucket.put.assert_called_with(
            "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/456",
            json={"title": "New concise title"},
        )

    def test_update_pull_request_reviewers(self, bitbucket):
        reviewers = ["alice", "bob"]
        bitbucket.update_pull_request_reviewers(
            "PROJ",
            "repo",
            789,
            reviewers,
        )
        bitbucket.put.assert_called_with(
            "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/789/reviewers",
            json={"reviewers": reviewers},
        )

    def test_update_pull_request_destination(self, bitbucket):
        bitbucket.update_pull_request_destination(
            "PROJ",
            "repo",
            987,
            "release/1.2.3",
        )
        bitbucket.put.assert_called_with(
            "/rest/api/1.0/projects/PROJ/repos/repo/pull-requests/987",
            json={"destination": {"branch": {"name": "release/1.2.3"}}},
        )

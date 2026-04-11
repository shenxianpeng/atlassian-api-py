from __future__ import annotations

import re
from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Bitbucket(AtlassianAPI):
    """Client for Bitbucket Server/Data Center REST API operations.

    Use this class for project repositories, branches, commits, pull requests,
    comments, build status, users, and tags. Methods that list Bitbucket
    resources automatically follow paginated ``values`` responses.

    .. seealso::
        `Bitbucket REST API Documentation <https://docs.atlassian.com/bitbucket-server/rest/7.12.1/bitbucket-rest.html>`_
    """

    def _get_paged(self, url: str, params: dict) -> list:
        """Collect all ``values`` from a paginated Bitbucket endpoint.

        :param url: Endpoint path to request.
        :type url: str
        :param params: Query parameters for pagination.
        :type params: dict
        :return: Combined values from each page. Returns an empty list when the
            response is missing ``values`` or cannot be parsed.
        :rtype: list
        """
        response = self.get(url, params=params)
        if (
            not isinstance(response, SimpleNamespace)
            or not hasattr(response, "values")
            or not response.values
        ):
            return []
        values = response.values
        limit = params.get("limit")
        while not response.isLastPage:
            if limit is not None:
                params["limit"] = limit - len(values)
                if params["limit"] < 0:
                    break
            params["start"] = response.nextPageStart
            response = self.get(url, params=params)
            if not isinstance(response, SimpleNamespace):
                break
            values += response.values or []
        return values

    def get_project_repo(
        self, project_key: str, start: int = 0, limit: int | None = None
    ) -> list:
        """Return repositories in a Bitbucket project.

        :param project_key: The key of the project.
        :type project_key: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Repository objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_project_repo_name(self, project_key: str) -> list[str]:
        """Return repository names for a Bitbucket project.

        :param project_key: The key of the project.
        :type project_key: str
        :return: Repository names.
        :rtype: list
        """
        values = self.get_project_repo(project_key)
        repo_name = []
        for value in values:
            repo_name.append(value.name)
        return repo_name

    def get_repo_info(
        self, project_key: str, repo_slug: str
    ) -> SimpleNamespace | str | None:
        """Return metadata for a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :return: Repository data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}"
        return self.get(url)

    def get_repo_branch(
        self, project_key: str, repo_slug: str, start: int = 0, limit: int | None = None
    ) -> list:
        """Return branches in a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Branch objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/branches"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def create_branch(
        self, project_key: str, repo_slug: str, branch_name: str, start_point: str
    ) -> dict | None:
        """Create a branch from an existing branch or commit.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the new branch.
        :type branch_name: str
        :param start_point: Source branch name or commit hash.
        :type start_point: str
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = (
            f"/rest/branch-utils/1.0/projects/{project_key}/repos/{repo_slug}/branches"
        )
        payload = {"name": branch_name, "startPoint": start_point}
        return self.post(url, json=payload)

    def delete_branch(
        self, project_key: str, repo_slug: str, branch_name: str, end_point: str
    ) -> dict | None:
        """Delete a branch from a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch to delete.
        :type branch_name: str
        :param end_point: Current commit hash for the branch deletion request.
        :type end_point: str
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/branch-utils/latest/projects/{project_key}/repos/{repo_slug}/branches"
        payload = {"name": branch_name, "endPoint": end_point}
        return self.delete(url, json=payload)

    def get_merged_branch(
        self, project_key: str, repo_slug: str, start: int = 0, limit: int | None = None
    ) -> list[str]:
        """Return branch names that Bitbucket marks as merged.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Merged branch display names.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/branches?base=refs/heads/master&details=true"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        branches = self._get_paged(url, params=params)

        merged_branch = []
        for branch in branches:
            pull_request = [
                x
                for x in dir(branch.metadata)
                if x.endswith("outgoing-pull-request-metadata")
            ]
            if pull_request:
                d_metadata = branch.metadata.__dict__
                metadata = d_metadata[
                    "com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata"
                ]
                try:
                    state = metadata.pullRequest.state
                except AttributeError:
                    state = None
                try:
                    merged = metadata.merged
                except AttributeError:
                    merged = None
                if state == "MERGED" or merged:
                    merged_branch.append(branch.displayId)
        return merged_branch

    def get_branch_commits(
        self,
        project_key: str,
        repo_slug: str,
        branch_name: str,
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return commits reachable from a branch.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch.
        :type branch_name: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Commit objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/commits/?until={branch_name}"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_state: str = "ALL",
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return pull requests for a repository.

        Common ``pr_state`` values include ``ALL``, ``OPEN``, ``MERGED``, and
        ``DECLINED``.
        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_state: The state of the pull request (default: ALL).
        :type pr_state: str, optional
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Pull request objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests?state={pr_state}"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_destination_branch_name(
        self, project_key: str, repo_slug: str, pr_id: int, limit: int = 0
    ) -> str | None:
        """Return the destination branch name for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Destination branch name, or ``None`` when the pull request is
            not found in the searched pages.
        :rtype: str or None
        """
        max_attempts = 100
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            limit += 25
            prs = self.get_pull_request(project_key, repo_slug, limit=limit)
            if not prs:
                return None
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.toRef.displayId
        return None

    def get_pull_request_source_branch_name(
        self, project_key: str, repo_slug: str, pr_id: int, limit: int = 0
    ) -> str | None:
        """Return the source branch name for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Source branch name, or ``None`` when the pull request is not
            found in the searched pages.
        :rtype: str or None
        """
        max_attempts = 100
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            limit += 25
            prs = self.get_pull_request(project_key, repo_slug, limit=limit)
            if not prs:
                return None
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.fromRef.displayId
        return None

    def get_pull_request_jira_key(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> str | None:
        """Extract a Jira issue key from a pull request source branch name.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: First ``PROJECT-123`` style key in the source branch, or
            ``None`` when no key is found.
        :rtype: str or None
        """
        source_branch_name = self.get_pull_request_source_branch_name(
            project_key, repo_slug, pr_id
        )
        if source_branch_name is None:
            return None
        match = re.search(r"[A-Z]+-[0-9]+", source_branch_name)
        if match is None:
            return None
        return match.group()

    def get_pull_request_id(
        self,
        project_key: str,
        repo_slug: str,
        pr_state: str = "OPEN",
        start: int = 0,
        limit: int | None = None,
    ) -> list[int]:
        """Return pull request IDs for a repository and state.

        Common ``pr_state`` values include ``OPEN``, ``ALL``, ``MERGED``, and
        ``DECLINED``.
        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_state: The state of the pull request (default: OPEN).
        :type pr_state: str, optional
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Pull request IDs.
        :rtype: list
        """
        prs = self.get_pull_request(
            project_key, repo_slug, pr_state=pr_state, start=start, limit=limit
        )
        pr_id = []
        for pr in prs:
            pr_id.append(pr.id)
        return pr_id

    def get_pull_request_overview(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return pull request metadata.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Pull request metadata as a ``SimpleNamespace``, raw response
            text for non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        return self.get(url)

    def get_pull_request_diff(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return the structured diff for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Diff data as a ``SimpleNamespace``, raw response text for
            non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/diff"
        return self.get(url)

    def get_pull_request_raw_diff(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return the raw unified diff for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Raw diff text, parsed JSON if Bitbucket returns JSON, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}.diff"
        return self.get(url)

    def get_pull_request_patch(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return the raw patch for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Raw patch text, parsed JSON if Bitbucket returns JSON, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}.patch"
        return self.get(url)

    def get_pull_request_commits(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return commits in a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Commit data as a ``SimpleNamespace``, raw response text for
            non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/commits"
        return self.get(url)

    def get_pull_request_activities(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return activity entries for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Activity objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_merge(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return mergeability information for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Merge data as a ``SimpleNamespace``, raw response text for
            non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace | str | None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/merge"
        return self.get(url)

    def get_branch_committer_info(
        self,
        project_key: str,
        repo_slug: str,
        branch_name: str,
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return committers for commits reachable from a branch.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch.
        :type branch_name: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Committer objects extracted from branch commits.
        :rtype: list
        """
        commits = self.get_branch_commits(
            project_key, repo_slug, branch_name, start=start, limit=limit
        )
        committer = []
        for commit in commits:
            committer.append(commit.committer)
        return committer

    def get_pull_request_comments(
        self, project_key: str, repo_slug: str, pr_id: int
    ) -> SimpleNamespace | str | None:
        """Return comments for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: Comment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/ui/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        return self.get(url)

    def add_pull_request_comment(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Add a general comment to a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text.
        :type comment: str
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        payload = {"text": comment}
        return self.post(url, json=payload)

    def add_pull_request_inline_comment(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        comment: str,
        path: str,
        line: int,
        line_type: str = "CONTEXT",
        file_type: str = "TO",
        src_path: str | None = None,
    ) -> dict | None:
        """Add an inline comment to a file and line in a pull request diff.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text.
        :type comment: str
        :param path: The path of the file to comment on (relative to the repo root).
        :type path: str
        :param line: The line number in the file to comment on.
        :type line: int
        :param line_type: Diff line type: ``CONTEXT``, ``ADDED``, or
            ``REMOVED``.
        :type line_type: str
        :param file_type: Diff side: ``FROM`` or ``TO``.
        :type file_type: str
        :param src_path: The path of the file in the source commit (for renames).
        :type src_path: str, optional
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        anchor: dict = {
            "line": line,
            "lineType": line_type,
            "fileType": file_type,
            "path": path,
        }
        if src_path is not None:
            anchor["srcPath"] = src_path
        payload = {"text": comment, "anchor": anchor}
        return self.post(url, json=payload)

    def update_pull_request_comment(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        old_comment: str,
        new_comment: str,
    ) -> dict | None:
        """Find a pull request comment by text and replace it.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param old_comment: Existing comment text to search for.
        :type old_comment: str
        :param new_comment: The new comment text.
        :type new_comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        activities = self.get_pull_request_activities(project_key, repo_slug, pr_id)
        comment_id = version = severity = state = None
        for activity in activities:
            try:
                if old_comment in activity.comment.text:
                    comment_id = activity.comment.id
                    version = activity.comment.version
                    severity = activity.comment.severity
                    state = activity.comment.state
                    break
            except AttributeError as e:
                logger.error(e)
        if not comment_id:
            return None
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{comment_id}"
        payload = {
            "version": version,
            "text": new_comment,
            "severity": severity,
            "state": state,
        }
        return self.put(url, json=payload)

    def delete_pull_request_comment(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Find a pull request comment by exact text and delete it.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text to be deleted.
        :type comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        activities = self.get_pull_request_activities(project_key, repo_slug, pr_id)
        comment_id = version = None
        for activity in activities:
            try:
                if comment == activity.comment.text:
                    comment_id = activity.comment.id
                    version = activity.comment.version
                    break
            except AttributeError as e:
                logger.error(e)
        if not comment_id:
            return None
        url = (
            f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{comment_id}"
            f"?version={version}"
        )
        return self.delete(url)

    def _find_comment_in_activities(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """
        Find a comment in pull request activities by matching text.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text to search for (substring match).
        :type comment: str
        :return: A dict with keys ``id``, ``version``, ``text``, ``severity``, and
            ``state`` when found, or ``None`` if no matching comment exists.
        :rtype: dict | None
        """
        activities = self.get_pull_request_activities(project_key, repo_slug, pr_id)
        for activity in activities:
            try:
                if comment in activity.comment.text:
                    return {
                        "id": activity.comment.id,
                        "version": activity.comment.version,
                        "text": activity.comment.text,
                        "severity": activity.comment.severity,
                        "state": activity.comment.state,
                    }
            except AttributeError as e:
                logger.error("Could not read comment from activity %s: %s", activity, e)
        return None

    def resolve_pull_request_comment(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Mark a pull request comment task as resolved.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: Comment text to search for.
        :type comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        found = self._find_comment_in_activities(project_key, repo_slug, pr_id, comment)
        if not found:
            return None
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{found['id']}"
        payload = {
            "version": found["version"],
            "text": found["text"],
            "severity": found["severity"],
            "state": "RESOLVED",
        }
        return self.put(url, json=payload)

    def reopen_pull_request_comment(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Reopen a resolved pull request comment task.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: Comment text to search for.
        :type comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        found = self._find_comment_in_activities(project_key, repo_slug, pr_id, comment)
        if not found:
            return None
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{found['id']}"
        payload = {
            "version": found["version"],
            "text": found["text"],
            "severity": found["severity"],
            "state": "OPEN",
        }
        return self.put(url, json=payload)

    def convert_comment_to_task(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Convert a pull request comment into a blocker task.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: Comment text to search for.
        :type comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        found = self._find_comment_in_activities(project_key, repo_slug, pr_id, comment)
        if not found:
            return None
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{found['id']}"
        payload = {
            "version": found["version"],
            "text": found["text"],
            "severity": "BLOCKER",
            "state": found["state"],
        }
        return self.put(url, json=payload)

    def convert_task_to_comment(
        self, project_key: str, repo_slug: str, pr_id: int, comment: str
    ) -> dict | None:
        """Convert a blocker task back to a regular pull request comment.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: Comment text to search for.
        :type comment: str
        :return: Decoded API response, or ``None`` when no matching comment is
            found or Bitbucket returns no body.
        :rtype: dict or None
        """
        found = self._find_comment_in_activities(project_key, repo_slug, pr_id, comment)
        if not found:
            return None
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{found['id']}"
        payload = {
            "version": found["version"],
            "text": found["text"],
            "severity": "NORMAL",
            "state": found["state"],
        }
        return self.put(url, json=payload)

    def get_file_change_history(
        self,
        project_key: str,
        repo_slug: str,
        branch_name: str,
        file_path: str,
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return commit history for a file on a branch.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch.
        :type branch_name: str
        :param file_path: The path of the file.
        :type file_path: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Commit history objects from the paginated ``values`` response.
        :rtype: list
        """
        url = (
            f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/commits?followRenames=true&path={file_path}&"
            f"until=refs%2Fheads%2F{branch_name}&start=0&avatarSize=32"
        )
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_file_content(
        self, project_key: str, repo_slug: str, branch_name: str, file_path: str
    ) -> SimpleNamespace | str | None:
        """Return raw file content from a branch.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch.
        :type branch_name: str
        :param file_path: The path of the file.
        :type file_path: str
        :return: Raw file content, parsed JSON if Bitbucket returns JSON, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/projects/{project_key}/repos/{repo_slug}/raw/{file_path}?at={branch_name}"
        return self.get(url)

    def get_build_status(self, commit_id: str) -> SimpleNamespace | str | None:
        """Return build status for a commit.

        :param commit_id: The ID of the commit.
        :type commit_id: str
        :return: Build status data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/build-status/latest/commits/{commit_id}"
        return self.get(url)

    def update_build_status(
        self,
        commit_id: str,
        build_state: str,
        data_key: str,
        build_name: str,
        build_url: str,
        description: str = "ManuallyCheckBuildPass",
    ) -> dict | None:
        """Create or update Bitbucket build status for a commit.

        :param commit_id: The ID of the commit.
        :type commit_id: str
        :param build_state: Build state, for example ``SUCCESSFUL`` or
            ``FAILED``.
        :type build_state: str
        :param data_key: Stable key identifying this build status.
        :type data_key: str
        :param build_name: The name of the build.
        :type build_name: str
        :param build_url: The URL of the build.
        :type build_url: str
        :param description: The description of the build.
        :type description: str
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/build-status/latest/commits/{commit_id}"
        payload = {
            "state": build_state,
            "key": data_key,
            "name": build_name,
            "url": build_url,
            "description": description,
        }
        return self.post(url, json=payload)

    def get_user(self, user_slug: str) -> SimpleNamespace | str | None:
        """Return Bitbucket user information by user slug.

        :param user_slug: The slug of the user.
        :type user_slug: str
        :return: User data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/latest/users/{user_slug}"
        return self.get(url)

    def review_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        user_slug: str,
        status: str = "APPROVED",
    ) -> dict | None:
        """Set a user's review status on a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param user_slug: The slug of the user.
        :type user_slug: str
        :param status: Review status. Common values are ``APPROVED``,
            ``UNAPPROVED``, and ``NEEDS_WORK``.
        :type status: str, optional
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/participants/{user_slug}"
        payload = {
            "status": f"{status}",  # status can be UNAPPROVED, NEEDS_WORK, or APPROVED
        }
        return self.put(url, json=payload)

    def update_pull_request_description(
        self, project_key: str, repo_slug: str, pr_id: int, new_description: str
    ) -> dict | None:
        """Replace a pull request description.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_description: The new description for the pull request.
        :type new_description: str
        :return: Decoded API response, or ``None`` when the pull request cannot
            be loaded or Bitbucket returns no body.
        :rtype: dict or None
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        if pr is None or isinstance(pr, str):
            return None
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "description": new_description}
        return self.put(url, json=payload)

    def update_pull_request_title(
        self, project_key: str, repo_slug: str, pr_id: int, new_title: str
    ) -> dict | None:
        """Replace a pull request title.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_title: The new title for the pull request.
        :type new_title: str
        :return: Decoded API response, or ``None`` when the pull request cannot
            be loaded or Bitbucket returns no body.
        :rtype: dict or None
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        if pr is None or isinstance(pr, str):
            return None
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "title": new_title}
        return self.put(url, json=payload)

    def update_pull_request_reviewers(
        self, project_key: str, repo_slug: str, pr_id: int, reviewers: list
    ) -> dict | None:
        """Replace the reviewer list for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param reviewers: Reviewer payload expected by Bitbucket.
        :type reviewers: list
        :return: Decoded API response, or ``None`` when the pull request cannot
            be loaded or Bitbucket returns no body.
        :rtype: dict or None
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        if pr is None or isinstance(pr, str):
            return None
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "reviewers": reviewers}
        return self.put(url, json=payload)

    def update_pull_request_destination(
        self, project_key: str, repo_slug: str, pr_id: int, new_destination: str
    ) -> dict | None:
        """Change the destination branch of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_destination: The new destination branch for the pull request.
        :type new_destination: str
        :return: Decoded API response, or ``None`` when the pull request cannot
            be loaded or Bitbucket returns no body.
        :rtype: dict or None
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        if pr is None or isinstance(pr, str):
            return None
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {
            "version": pr.version,
            "destination": {"branch": {"name": new_destination}},
        }
        return self.put(url, json=payload)

    def create_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        title: str,
        from_branch: str,
        to_branch: str,
        description: str | None = None,
        reviewers: list[str] | None = None,
    ) -> dict | None:
        """Create a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param title: The title of the pull request.
        :type title: str
        :param from_branch: The source branch name.
        :type from_branch: str
        :param to_branch: The destination branch name.
        :type to_branch: str
        :param description: An optional description for the pull request.
        :type description: str, optional
        :param reviewers: Optional reviewer user slugs.
        :type reviewers: list[str], optional
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests"
        payload: dict = {
            "title": title,
            "fromRef": {"id": f"refs/heads/{from_branch}"},
            "toRef": {"id": f"refs/heads/{to_branch}"},
        }
        if description is not None:
            payload["description"] = description
        if reviewers:
            payload["reviewers"] = [{"user": {"slug": slug}} for slug in reviewers]
        return self.post(url, json=payload)

    def merge_pull_request(
        self, project_key: str, repo_slug: str, pr_id: int, pr_version: int
    ) -> dict | None:
        """Merge a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param pr_version: Current pull request version required by Bitbucket
            optimistic locking.
        :type pr_version: int
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/merge"
        params = {"version": pr_version}
        return self.post(url, params=params)

    def decline_pull_request(
        self, project_key: str, repo_slug: str, pr_id: int, pr_version: int
    ) -> dict | None:
        """Decline a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param pr_version: Current pull request version required by Bitbucket
            optimistic locking.
        :type pr_version: int
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/decline"
        params = {"version": pr_version}
        return self.post(url, params=params)

    def get_tags(
        self,
        project_key: str,
        repo_slug: str,
        start: int = 0,
        limit: int | None = None,
    ) -> list:
        """Return tags for a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: Tag objects from the paginated ``values`` response.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/tags"
        params: dict = {}
        if start is not None and start > 0:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def create_tag(
        self,
        project_key: str,
        repo_slug: str,
        tag_name: str,
        start_point: str,
        message: str | None = None,
    ) -> dict | None:
        """Create a lightweight or annotated tag in a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param tag_name: The name of the tag to create.
        :type tag_name: str
        :param start_point: The commit SHA or branch name to tag.
        :type start_point: str
        :param message: Optional message for an annotated tag.
        :type message: str, optional
        :return: Decoded API response, or ``None`` when Bitbucket returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/tags"
        payload: dict = {"name": tag_name, "startPoint": start_point}
        if message is not None:
            payload["message"] = message
        return self.post(url, json=payload)

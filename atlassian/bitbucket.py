import re
from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Bitbucket(AtlassianAPI):
    """
    Bitbucket API Reference

    .. seealso::
        `Bitbucket REST API Documentation <https://docs.atlassian.com/bitbucket-server/rest/7.12.1/bitbucket-rest.html>`_
    """

    def _get_paged(self, url, params):
        """
        Retrieve paginated results from the Bitbucket API.

        :param url: The API endpoint URL.
        :type url: str
        :param params: Query parameters for pagination.
        :type params: dict
        :return: A list of paginated results.
        :rtype: list
        """
        response = self.get(url, params=params)
        if response.values:
            values = response.values
        else:
            return []
        limit = params.get("limit")
        while not response.isLastPage:
            if limit is not None:
                params["limit"] = limit - len(values)
                if params["limit"] < 0:
                    break
            params["start"] = response.nextPageStart
            response = self.get(url, params=params)
            values += response.values or {}
        return values

    def get_project_repo(self, project_key, start=0, limit=None):
        """
        Retrieve repositories for a specific project.

        :param project_key: The key of the project.
        :type project_key: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: A list of repositories in the project.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_project_repo_name(self, project_key):
        """
        Retrieve the names of all repositories in a project.

        :param project_key: The key of the project.
        :type project_key: str
        :return: A list of repository names.
        :rtype: list
        """
        values = self.get_project_repo(project_key)
        repo_name = []
        for value in values:
            repo_name.append(value.name)
        return repo_name

    def get_repo_info(self, project_key, repo_slug):
        """
        Retrieve information about a specific repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :return: A dictionary containing repository information.
        :rtype: dict
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}"
        return self.get(url)

    def get_repo_branch(self, project_key, repo_slug, start=0, limit=None):
        """
        Retrieve branches for a specific repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: A list of branches in the repository.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/branches"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def create_branch(self, project_key, repo_slug, branch_name, start_point):
        """
        Create a new branch in a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the new branch.
        :type branch_name: str
        :param start_point: The starting point for the branch (e.g., a commit hash or branch name).
        :type start_point: str
        :return: The response from the API.
        :rtype: dict
        """
        url = (
            f"/rest/branch-utils/1.0/projects/{project_key}/repos/{repo_slug}/branches"
        )
        payload = {"name": branch_name, "startPoint": start_point}
        return self.post(url, json=payload)

    def delete_branch(self, project_key, repo_slug, branch_name, end_point):
        """
        Delete a branch from a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch to delete.
        :type branch_name: str
        :param end_point: The endpoint for the branch deletion.
        :type end_point: str
        :return: The response from the API.
        :rtype: dict
        """
        url = f"/rest/branch-utils/latest/projects/{project_key}/repos/{repo_slug}/branches"
        payload = {"name": branch_name, "endPoint": end_point}
        return self.delete(url, json=payload)

    def get_merged_branch(self, project_key, repo_slug, start=0, limit=None):
        """
        Retrieve the names of merged branches in a repository.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param start: The starting index for pagination (optional).
        :type start: int, optional
        :param limit: The maximum number of results to return (optional).
        :type limit: int, optional
        :return: A list of merged branch names.
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
        self, project_key, repo_slug, branch_name, start=0, limit=None
    ):
        """
        Get a specific branch commits.

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
        :return: A list of commits in the branch.
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
        self, project_key, repo_slug, pr_state="ALL", start=0, limit=None
    ):
        """
        Get ALL pull requests.

        By default: pr_state is ALL, other states are PEN, MERGED, DECLINED
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
        :return: A list of pull requests.
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
        self, project_key, repo_slug, pr_id, limit=0
    ):
        """
        Get a pull request destination branch name.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: The destination branch name associated with the pull request.
        :rtype: str"""
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_slug, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.toRef.displayId
        return None

    def get_pull_request_source_branch_name(
        self, project_key, repo_slug, pr_id, limit=0
    ):
        """
        Get a pull request source branch name.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: The source branch name associated with the pull request.
        :rtype: str"""
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_slug, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.fromRef.displayId
        return None

    def get_pull_request_jira_key(self, project_key, repo_slug, pr_id):
        """
        Get a pull request Jira ticket key.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: The Jira ticket key associated with the pull request.
        :rtype: str
        """
        source_branch_name = self.get_pull_request_source_branch_name(
            project_key, repo_slug, pr_id
        )
        try:
            jira_key = re.search(r"[A-Z]+-[0-9]+", source_branch_name).group()
            return jira_key
        except AttributeError as e:
            logger.error(e)

    def get_pull_request_id(
        self, project_key, repo_slug, pr_state="OPEN", start=0, limit=None
    ):
        """
        Get a specific pull request ID.

        By default: pr_state is OPEN, other states are ALL, MERGED, DECLINED
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
        :return: A list of pull request IDs.
        :rtype: list
        """
        prs = self.get_pull_request(
            project_key, repo_slug, pr_state=pr_state, start=start, limit=limit
        )
        pr_id = []
        for pr in prs:
            pr_id.append(pr.id)
        return pr_id

    def get_pull_request_overview(self, project_key, repo_slug, pr_id):
        """
        Get a specific pull request overview.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A dictionary containing pull request overview information.
        :rtype: dict
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        return self.get(url)

    def get_pull_request_diff(self, project_key, repo_slug, pr_id):
        """
        Get streams a diff within a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A dictionary containing pull request diff information.
        :rtype: dict
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/diff"
        return self.get(url)

    def get_pull_request_raw_diff(self, project_key, repo_slug, pr_id) -> str:
        """
        Get streams the raw diff for a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A string containing pull request diff information.
        :rtype: str
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}.diff"
        return self.get(url)

    def get_pull_request_patch(self, project_key, repo_slug, pr_id) -> str:
        """
        Get streams a patch representing a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A string containing pull request diff information.
        :rtype: str
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}.patch"
        return self.get(url)

    def get_pull_request_commits(self, project_key, repo_slug, pr_id):
        """
        Get a specific pull request commits.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A list of commits in the pull request.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/commits"
        return self.get(url)

    def get_pull_request_activities(
        self, project_key, repo_slug, pr_id, start=0, limit=None
    ):
        """
        Get a specific pull request activities information.

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
        :return: A list of pull request activities.
        :rtype: list
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_merge(self, project_key, repo_slug, pr_id):
        """
        Get the specific Pull Request merge information.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A dictionary containing pull request merge information.
        :rtype: dict
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/merge"
        return self.get(url) or {}

    def get_branch_committer_info(
        self, project_key, repo_slug, branch_name, start=0, limit=None
    ):
        """
        Get branch committer information.

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
        :return: A list of committers in the branch.
        :rtype: list
        """
        commits = self.get_branch_commits(
            project_key, repo_slug, branch_name, start=start, limit=limit
        )
        committer = []
        for commit in commits:
            committer.append(commit.committer)
        return committer

    def get_pull_request_comments(self, project_key, repo_slug, pr_id):
        """
        Get a specific pull request all comments.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :return: A list of comments in the pull request.
        :rtype: list
        """
        url = f"/rest/ui/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        return self.get(url)

    def add_pull_request_comment(self, project_key, repo_slug, pr_id, comment):
        """
        Add comment to a specific pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text.
        :type comment: str
        :return: The response from the API.
        :rtype: dict
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        payload = {"text": comment}
        return self.post(url, json=payload)

    def update_pull_request_comment(
        self, project_key, repo_slug, pr_id, old_comment, new_comment
    ):
        """
        Update a specific comment of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param old_comment: The old comment text to be updated.
        :type old_comment: str
        :param new_comment: The new comment text.
        :type new_comment: str
        :return: The response from the API.
        :rtype: dict
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
            return
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{comment_id}"
        payload = {
            "version": version,
            "text": new_comment,
            "severity": severity,
            "state": state,
        }
        return self.put(url, json=payload)

    def delete_pull_request_comment(self, project_key, repo_slug, pr_id, comment):
        """
        Delete comment from a specific pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param comment: The comment text to be deleted.
        :type comment: str
        :return: The response from the API.
        :rtype: dict
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
            return
        url = (
            f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments/{comment_id}"
            f"?version={version}"
        )
        return self.delete(url) or {}

    def get_file_change_history(
        self, project_key, repo_slug, branch_name, file_path, start=0, limit=None
    ):
        """
        Get a specific file change histories.

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
        :return: A list of file change histories.
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

    def get_file_content(self, project_key, repo_slug, branch_name, file_path):
        """
        Get file content from a specific branch.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param branch_name: The name of the branch.
        :type branch_name: str
        :param file_path: The path of the file.
        :type file_path: str
        :return: The content of the file.
        :rtype: str
        """
        url = f"/projects/{project_key}/repos/{repo_slug}/raw/{file_path}?at={branch_name}"
        return self.get(url)

    def get_build_status(self, commit_id):
        """
        Get build status.

        :param commit_id: The ID of the commit.
        :type commit_id: str
        :return: A dictionary containing build status information.
        :rtype: dict
        """
        url = f"/rest/build-status/latest/commits/{commit_id}"
        return self.get(url) or {}

    def update_build_status(
        self,
        commit_id,
        build_state,
        data_key,
        build_name,
        build_url,
        description="ManuallyCheckBuildPass",
    ):
        """
        Update build status.

        :param commit_id: The ID of the commit.
        :type commit_id: str
        :param build_state: The state of the build.
        :type build_state: str
        :param data_key: The key of the data.
        :type data_key: str
        :param build_name: The name of the build.
        :type build_name: str
        :param build_url: The URL of the build.
        :type build_url: str
        :param description: The description of the build.
        :type description: str
        """
        url = f"/rest/build-status/latest/commits/{commit_id}"
        payload = {
            "state": build_state,
            "key": data_key,
            "name": build_name,
            "url": build_url,
            "description": description,
        }
        self.post(url, json=payload)

    def get_user(self, user_slug):
        """
        Get user information.

        :param user_slug: The slug of the user.
        :type user_slug: str
        :return: A dictionary containing user information.
        :rtype: dict
        """
        url = f"/rest/api/latest/users/{user_slug}"
        return self.get(url)

    def review_pull_request(
        self, project_key, repo_slug, pr_id, user_slug, status="APPROVED"
    ):
        """
        Review a pull request as the current user.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param user_slug: The slug of the user.
        :type user_slug: str
        :param status: The status of the review (default: APPROVED).
        :type status: str, optional
        :return: The response from the API.
        :rtype: dict
        """
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/participants/{user_slug}"
        payload = {
            "status": f"{status}",  # status can be UNAPPROVED, NEEDS_WORK, or APPROVED
        }
        return self.put(url, json=payload)

    def update_pull_request_description(
        self, project_key, repo_slug, pr_id, new_description
    ):
        """
        Update the description of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_description: The new description for the pull request.
        :type new_description: str
        :return: The response from the API.
        :rtype: dict
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "description": new_description}
        return self.put(url, json=payload)

    def update_pull_request_title(self, project_key, repo_slug, pr_id, new_title):
        """
        Update the title of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_title: The new title for the pull request.
        :type new_title: str
        :return: The response from the API.
        :rtype: dict
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "title": new_title}
        return self.put(url, json=payload)

    def update_pull_request_reviewers(self, project_key, repo_slug, pr_id, reviewers):
        """
        Update the reviewers of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param reviewers: A list of user slugs to add as reviewers.
        :type reviewers: list
        :return: The response from the API.
        :rtype: dict
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {"version": pr.version, "reviewers": reviewers}
        return self.put(url, json=payload)

    def update_pull_request_destination(
        self, project_key, repo_slug, pr_id, new_destination
    ):
        """
        Update the destination branch of a pull request.

        :param project_key: The key of the project.
        :type project_key: str
        :param repo_slug: The slug of the repository.
        :type repo_slug: str
        :param pr_id: The ID of the pull request.
        :type pr_id: int
        :param new_destination: The new destination branch for the pull request.
        :type new_destination: str
        :return: The response from the API.
        :rtype: dict
        """
        pr = self.get_pull_request_overview(project_key, repo_slug, pr_id)
        url = f"/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        payload = {
            "version": pr.version,
            "destination": {"branch": {"name": new_destination}},
        }
        return self.put(url, json=payload)

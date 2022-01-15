import re
from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Bitbucket(AtlassianAPI):
    """https://docs.atlassian.com/bitbucket-server/rest/7.12.1/bitbucket-rest.html"""

    def _get_paged(self, url, params):
        """Get more pages"""
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
        """Get a specific project repository"""
        url = f"/rest/api/latest/projects/{project_key}/repos/"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_project_repo_name(self, project_key):
        """Get repository name"""
        values = self.get_project_repo(project_key)
        repo_name = []
        for value in values:
            repo_name.append(value.name)
        return repo_name

    def get_repo_info(self, project_key, repo_key):
        """Get repository information"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}"
        return self.get(url)

    def get_repo_branch(self, project_key, repo_key, start=0, limit=None):
        """Get repository branch"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/branches"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def create_branch(self, project_key, repo_key, branch_name, start_point):
        """Create a branch
        Using service account to create branch failed because of issue https://jira.atlassian.com/browse/BSERV-9340
        """
        url = f"/rest/branch-utils/1.0/projects/{project_key}/repos/{repo_key}/branches"
        json = {"name": branch_name, "startPoint": start_point}
        return self.post(url, json=json)

    def delete_branch(self, project_key, repo_key, branch_name, end_point):
        """Delete a branch"""
        url = f"/rest/branch-utils/latest/projects/{project_key}/repos/{repo_key}/branches"
        json = {"name": branch_name, "endPoint": end_point}
        return self.delete(url, json=json)

    def get_merged_branch(self, project_key, repo_key, start=0, limit=None):
        """Get the merged branch names"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/branches?base=refs/heads/master&details=true"
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
        self, project_key, repo_key, branch_name, start=0, limit=None
    ):
        """Get a specific branch commits"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/commits/?until={branch_name}"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request(
        self, project_key, repo_key, pr_state="ALL", start=0, limit=None
    ):
        """Get ALL pull requests.
        By default: pr_state is ALL, other states are PEN, MERGED, DECLINED
        """
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/pull-requests?state={pr_state}"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_destination_branch_name(
        self, project_key, repo_key, pr_id, limit=0
    ):
        """Get a pull request destination branch name"""
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_key, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.toRef.displayId
        return None

    def get_pull_request_source_branch_name(
        self, project_key, repo_key, pr_id, limit=0
    ):
        """Get a pull request source branch name"""
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_key, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.fromRef.displayId
        return None

    def get_pull_request_relate_jira_key(self, project_key, repo_key, pr_id):
        """Get a pull request relate Jira ticket key"""
        source_branch_name = self.get_pull_request_source_branch_name(
            project_key, repo_key, pr_id
        )
        try:
            jira_key = re.search(r"[A-Z]+-[0-9]+", source_branch_name).group()
            return jira_key
        except AttributeError as e:
            logger.error(e)

    def get_pull_request_id(
        self, project_key, repo_key, pr_state="OPEN", start=0, limit=None
    ):
        """Get a specific pull request ID. By default: pr_state is OPEN, other states are ALL, MERGED, DECLINED"""
        prs = self.get_pull_request(
            project_key, repo_key, pr_state=pr_state, start=start, limit=limit
        )
        pr_id = []
        for pr in prs:
            pr_id.append(pr.id)
        return pr_id

    def get_pull_request_overview(self, project_key, repo_key, pr_id):
        """Get a specific pull request overview"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/pull-requests/{pr_id}"
        return self.get(url)

    def get_pull_request_diff(self, project_key, repo_key, pr_id):
        """Get a specific pull request diff"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/pull-requests/{pr_id}/diff"
        return self.get(url)

    def get_pull_request_commits(self, project_key, repo_key, pr_id):
        """Get a specific pull request commits"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/pull-requests/{pr_id}/commits"
        return self.get(url)

    def get_pull_request_activities(
        self, project_key, repo_slug, pr_id, start=0, limit=None
    ):
        """Get a specific pull request activities information"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities"
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_merge(self, project_key, repo_key, pr_id):
        """Get the specific Pull Request merge information"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/pull-requests/{pr_id}/merge"
        return self.get(url) or {}

    def get_branch_committer_info(
        self, project_key, repo_key, branch_name, start=0, limit=None
    ):
        """Get branch committer information"""
        commits = self.get_branch_commits(
            project_key, repo_key, branch_name, start=start, limit=limit
        )
        committer = []
        for commit in commits:
            committer.append(commit.committer)
        return committer

    def get_pull_request_comments(self, project_key, repo_key, pr_id):
        """Get a specific pull request all comments"""
        url = f"/rest/ui/latest/projects/{project_key}/repos/{repo_key}/pull-requests/{pr_id}/comments"
        return self.get(url)

    def add_pull_request_comment(self, project_key, repo_slug, pr_id, comment):
        """Add comment to a specific pull request"""
        url = f"/rest/api/latest/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"
        json = {"text": comment}
        return self.post(url, json=json)

    def update_pull_request_comment(
        self, project_key, repo_slug, pr_id, old_comment, new_comment
    ):
        """Update a specific comment of a pull request"""
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
        json = {
            "version": version,
            "text": new_comment,
            "severity": severity,
            "state": state,
        }
        return self.put(url, json=json)

    def delete_pull_request_comment(self, project_key, repo_slug, pr_id, comment):
        """Delete comment from a specific pull request"""
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
        self, project_key, repo_key, branch_name, file_path, start=0, limit=None
    ):
        """Get a specific file change histories"""
        url = (
            f"/rest/api/latest/projects/{project_key}/repos/{repo_key}/commits?followRenames=true&path={file_path}&"
            f"until=refs%2Fheads%2F{branch_name}&start=0&avatarSize=32"
        )
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params["limit"] = limit
        return self._get_paged(url, params=params)

    def get_file_content(self, project_key, repo_key, branch_name, file_path):
        """Get file content from a specific branch"""
        url = (
            f"/projects/{project_key}/repos/{repo_key}/raw/{file_path}?at={branch_name}"
        )
        return self.get(url)

    def get_build_status(self, commit_id):
        """Get bulid status"""
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
        """Update bulid status"""
        url = f"/rest/build-status/latest/commits/{commit_id}"
        json = {
            "state": build_state,
            "key": data_key,
            "name": build_name,
            "url": build_url,
            "description": description,
        }
        self.post(url, json=json)

    def get_user(self, user_slug):
        """Get user information"""
        url = f"/rest/api/latest/users/{user_slug}"
        return self.get(url)

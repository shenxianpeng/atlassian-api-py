import re
from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Bitbucket(AtlassianAPI):
    """https://docs.atlassian.com/bitbucket-server/rest/7.12.1/bitbucket-rest.html"""

    def _get_paged(self, url, params):
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
        url = '/rest/api/latest/projects/{}/repos/'.format(project_key)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
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
        url = '/rest/api/latest/projects/{}/repos/{}'.format(project_key, repo_key)
        return self.get(url)

    def get_repo_branch(self, project_key, repo_key, start=0, limit=None):
        url = '/rest/api/latest/projects/{}/repos/{}/branches'.format(project_key, repo_key)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def create_branch(self, project_key, repo_key, branch_name, start_point):
        """Create a branch"""
        """Using service account to create branch failed because of
        this issue https://jira.atlassian.com/browse/BSERV-9340"""
        url = '/rest/branch-utils/1.0/projects/{}/repos/{}/branches'.format(project_key, repo_key)
        json = {"name": branch_name, "startPoint": start_point}
        return self.post(url, json=json)

    def delete_branch(self, project_key, repo_key, branch_name, end_point):
        """Delete a branch"""
        url = '/rest/branch-utils/latest/projects/{}/repos/{}/branches'.format(project_key, repo_key)
        json = {"name": branch_name, "endPoint": end_point}
        return self.delete(url, json=json)

    def get_merged_branch(self, project_key, repo_key, start=0, limit=None):
        """Get merged branch names"""
        url = '/rest/api/latest/projects/{}/repos/{}/branches?base=refs/heads/master&details=true'.\
            format(project_key, repo_key)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        branches = self._get_paged(url, params=params)

        merged_branch = []
        for branch in branches:
            pull_request = [x for x in dir(branch.metadata) if x.endswith('outgoing-pull-request-metadata')]
            if pull_request:
                d_metadata = branch.metadata.__dict__
                metadata = d_metadata[
                    'com.atlassian.bitbucket.server.bitbucket-ref-metadata:outgoing-pull-request-metadata']
                try:
                    state = metadata.pullRequest.state
                except AttributeError:
                    state = None
                try:
                    merged = metadata.merged
                except AttributeError:
                    merged = None
                if state == 'MERGED' or merged:
                    merged_branch.append(branch.displayId)
        return merged_branch

    def get_branch_commits(self, project_key, repo_key, branch_name, start=0, limit=None):
        """Get a specific branch commits"""
        url = '/rest/api/latest/projects/{}/repos/{}/commits/?until={}'.format(project_key, repo_key, branch_name)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_pull_request(self, project_key, repo_key, pr_state="ALL", start=0, limit=None):
        """
        Get ALL pull requests.
        By default: pr_state is ALL, other states are PEN, MERGED, DECLINED
        """
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests?state={}'.format(project_key, repo_key, pr_state)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_destination_branch_name(self, project_key, repo_key, pr_id, limit=0):
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_key, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.toRef.displayId
            return None

    def get_pull_request_source_branch_name(self, project_key, repo_key, pr_id, limit=0):
        while True:
            limit += 25
            prs = self.get_pull_request(project_key, repo_key, limit=limit)
            for pr in prs:
                if pr.id == int(pr_id):
                    return pr.fromRef.displayId
            return None

    def get_pull_request_relate_jira_key(self, project_key, repo_key, pr_id):
        """Get the pull request relate Jira ticket key"""
        source_branch_name = self.get_pull_request_source_branch_name(project_key, repo_key, pr_id)
        try:
            jira_key = re.search(r'[A-Z]+-[0-9]+', source_branch_name).group()
            return jira_key
        except AttributeError as e:
            logger.error(e)

    def get_pull_request_id(self, project_key, repo_key, pr_state="OPEN", start=0, limit=None):
        """By default: pr_state is OPEN, other states are ALL, MERGED, DECLINED"""
        prs = self.get_pull_request(project_key, repo_key, pr_state=pr_state, start=start, limit=limit)
        pr_id = []
        for pr in prs:
            pr_id.append(pr.id)
        return pr_id

    def get_pull_request_overview(self, project_key, repo_key, pr_id):
        """A specific pull request overview"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}'.format(project_key, repo_key, pr_id)
        return self.get(url)

    def get_pull_request_diff(self, project_key, repo_key, pr_id):
        """A specific pull request diff"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/diff'.format(project_key, repo_key, pr_id)
        return self.get(url)

    def get_pull_request_commits(self, project_key, repo_key, pr_id):
        """A specific pull request commits"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/commits'.format(project_key, repo_key, pr_id)
        return self.get(url)

    def get_pull_request_comments(self, project_key, repo_key, pr_id):
        """A specific pull request comments"""
        url = '/rest/ui/latest/projects/{}/repos/{}/pull-requests/{}/comments'.format(project_key, repo_key, pr_id)
        return self.get(url)

    def get_pull_request_activities(self, project_key, repo_slug, pr_id, start=0, limit=None):
        """A specific pull request activities"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/activities'.format(project_key, repo_slug, pr_id)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_pull_request_merge(self, project_key, repo_key, pr_id):
        """Get the specific Pull Request merge information"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/merge'.format(project_key, repo_key, pr_id)
        return self.get(url) or {}

    def get_branch_committer_info(self, project_key, repo_key, branch_name, start=0, limit=None):
        commits = self.get_branch_commits(project_key, repo_key, branch_name, start=start, limit=limit)
        committer = []
        for commit in commits:
            committer.append(commit.committer)
        return committer

    def add_comment_to_pull_request(self, project_key, repo_slug, pr_id, comment):
        """Add comment to a specific pull request"""
        url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/comments?' \
              'diffType=EFFECTIVE&markup=true&avatarSize=64'.format(project_key, repo_slug, pr_id)
        json = {"text": comment}
        return self.post(url, json=json)

    # TODO not work
    def remove_comment_from_pull_request(self, project_key, repo_slug, pr_id, comment):
        """Delete comment from a specific pull request"""
        comment_values = self.get_pull_request_activities(project_key, repo_slug, pr_id)
        commit_id = None
        for comment_value in comment_values:
            try:
                if comment == comment_value.comment.text:
                    commit_id = comment_value.comment.id
                    break
            except AttributeError:
                pass
        if commit_id:
            url = '/rest/api/latest/projects/{}/repos/{}/pull-requests/{}/comments/{}?VERSION'.format(
                project_key, repo_slug, pr_id, commit_id)
            return self.delete(url) or {}

    def get_file_change_history(self, project_key, repo_key, branch_name, file_path, start=0, limit=None):
        """Get a specific file change histories"""
        url = '/rest/api/latest/projects/{}/repos/{}/commits?followRenames=true&path={}&' \
              'until=refs%2Fheads%2F{}&start=0&avatarSize=32'.format(project_key, repo_key, file_path, branch_name)
        params = {}
        if start:
            params["start"] = start
        if limit is not None:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_file_content(self, project_key, repo_key, branch_name, file_path):
        """Get file content from a specific branch"""
        url = '/projects/{}/repos/{}/raw/{}?at={}'.format(project_key, repo_key, file_path, branch_name)
        return self.get(url)

    def get_build_status(self, commit_id):
        url = '/rest/build-status/latest/commits/{}'.format(commit_id)
        return self.get(url) or {}

    def update_build_status(self, commit_id,
                            build_state,
                            data_key,
                            build_name,
                            build_url,
                            description="ManuallyCheckBuildPass"):

        url = '/rest/build-status/latest/commits/{}'.format(commit_id)
        json = {
            "state": build_state,
            "key": data_key,
            "name": build_name,
            "url": build_url,
            "description": description
        }
        self.post(url, json=json)


import configparser
from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Bitbucket(AtlassianAPI):

    def _get_paged(self, url, params):
        response = self.get(url, params=params)
        if "values" not in response:
            return []
        values = (response or {}).get("values", [])
        limit = params.get("limit")
        while not response.get("isLastPage"):
            if limit is not None:
                params["limit"] = limit - len(values)
                if params["limit"] < 0:
                    break
            params["start"] = response.get("nextPageStart")
            response = self.get(url, params=params)
            values += (response or {}).get("values", [])
        return values

    def get_project_repo(self, project_key, start=0, limit=None):
        url = '/rest/api/latest/projects/{0}/repos/'.format(project_key)
        params = {}
        if start:
            params["start"] = start
        if limit:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_project_repo_name(self, project_key):
        values = self.get_project_repo(project_key)
        repo_names = []
        for value in values:
            repo_names.append(value['name'])
        return repo_names

    def get_repo_info(self, project_key, repo_key):
        url = '/rest/api/latest/projects/{0}/repos/{1}'.format(project_key, repo_key)
        return self.get(url)

    def get_repo_branch(self, project_key, repo_key, start=0, limit=None):
        url = '/rest/api/latest/projects/{0}/repos/{1}/branches'.format(project_key, repo_key)
        params = {}
        if start:
            params["start"] = start
        if limit:
            params['limit'] = limit
        return self._get_paged(url, params=params)

    def get_repo_branch_names(self, project_key, repo_key):
        values = self.get_repo_branch(project_key, repo_key)
        branch_names = []
        for value in values:
            branch_names.append(value['displayId'])
        return branch_names

    def get_branch_latest_commit(self, project_key, repo_key, branch_name):
        branches = self.get_repo_branch(project_key, repo_key)
        for branch in branches:
            if branch_name == branch['displayId']:
                return branch['latestCommit']

    def create_branch(self, project_key, repo_key, branch_name, start_point):
        """This func not work cause of this issue https://jira.atlassian.com/browse/BSERV-9340"""
        url = '/rest/branch-utils/1.0/projects/{0}/repos/{1}/branches'.format(project_key, repo_key)
        json = {"name": branch_name, "startPoint": start_point}
        return self.post(url, json=json)

    def delete_branch(self, project_key, repo_key, branch_name, end_point):
        url = '/rest/branch-utils/latest/projects/{0}/repos/{1}/branches'.format(project_key, repo_key)
        json = {"name": branch_name, "endPoint": end_point}
        return self.delete(url, json=json)

    def get_merged_branch(self, project_key, repo_key, start=0, limit=None):
        url = '/rest/api/latest/projects/{0}/repos/{1}/branches?base=refs/heads/master'.format(project_key, repo_key)
        params = {}
        if start:
            params["start"] = start
        if limit:
            params['limit'] = limit
        return self._get_paged(url, params=params)

        merged_branches = []
        for branch in branches:
            for ojb_key, ojb_value in branch.items():
                if ojb_key == 'metadata':
                    for metadata_key, metadata_value in ojb_value.items():
                        if 'outgoing-pull-request-metadata' in metadata_key and 'pullRequest' in metadata_value \
                                and metadata_value['pullRequest']['state'] == 'MERGED':
                            if branch['displayId'] not in merged_branches:
                                merged_branches.append(branch['displayId'])
                                return merged_branches


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    git_url = config['bitbucket']['url']
    git_usr = config['bitbucket']['username']
    git_psw = config['bitbucket']['password']

    git = Bitbucket(url=git_url, username=git_usr, password=git_psw)
    ret = git.get_merged_branch("MVAS", "uvuddb")
    print(ret)
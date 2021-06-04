import unittest
import configparser
from atlassian import Bitbucket

config = configparser.ConfigParser()
config.read('config.ini')

git_url = config['bitbucket']['url']
git_usr = config['bitbucket']['username']
git_psw = config['bitbucket']['password']


class TestBitbucket(unittest.TestCase):

    def setUp(self):
        self.git = Bitbucket(url=git_url, username=git_usr, password=git_psw)

    def test_get_project_repo(self):
        repos = self.git.get_project_repo('MVAS')
        self.assertGreaterEqual(len(repos), 36)

    def test_get_project_repo_name(self):
        repo_names = self.git.get_project_repo_name('MVAS')
        exist_repos = ['uvuddb', 'uvuddb-ud82', 'uvuddb-uv113']
        for repo in exist_repos:
            self.assertIn(repo, repo_names)

    def test_get_repo_info(self):
        repo_info = self.git.get_repo_info('MVAS', 'uvuddb')
        self.assertEqual(repo_info.slug, 'uvuddb')
        self.assertEqual(repo_info.project.name, 'MV Application Server')

    def test_get_repo_branch(self):
        """assert the branch latest commit and these branches exist."""
        branches = self.git.get_repo_branch('MVAS', 'uvuddb')
        branch_names = []
        for branch in branches:
            branch_names.append(branch.displayId)
            if branch.displayId == 'hotfix/12.1.1.HF1':
                self.assertEqual(branch.latestCommit, 'da7696ceacaff863d40a3215eea08e661d5b1c5a')
        exist_branches = ['hotfix/12.1.1.HF1', 'hotfix/12.1.1.HF2', 'hotfix/12.1.1.HF3', 'hotfix/12.1.1.HF4']
        for branch in exist_branches:
            self.assertIn(branch, branch_names)

    def test_create_delete_branch(self):
        # Create branch failed because of When performing a ref operation, the author must have an e-mail address.
        self.git.create_branch('MVAS', 'uvuddb', 'feature/create_branch_with_rest_api', 'da7696ceacaff')
        branch_names = self.git.get_repo_branch_names('MVAS', 'uvuddb')
        self.assertNotIn('feature/create_branch_with_rest_api', branch_names)
        self.git.delete_branch('MVAS', 'uvuddb', 'feature/create_branch_with_rest_api', 'da7696ceacaff')
        self.assertNotIn('feature/create_branch_with_rest_api', branch_names)

    def test_get_merged_branch(self):
        merged_branches = self.git.get_merged_branch('MVAS', 'uvuddb')
        print(merged_branches)
        self.assertIn('hotfix/12.1.1.HF6', merged_branches)

    def test_get_branch_commits(self):
        commits = self.git.get_branch_commits('MVAS', 'uvuddb', 'hotfix/12.1.1.HF1', limit=1)
        exist_commits = ['da7696ceaca', '9e6af338697']
        for commit in commits:
            self.assertIn(commit.displayId, exist_commits)

    def test_get_branch_committer_info(self):
        all_committer = self.git.get_branch_committer_info('MVAS', 'uvuddb', 'hotfix/12.1.1.HF1', limit=0)
        for committer in all_committer:
            self.assertEqual('Xianpeng Shen', committer.displayName)

    def test_get_pull_request(self):
        pull_requests = self.git.get_pull_request('MVAS', 'uvuddb', limit=1)
        self.assertEqual(len(pull_requests), 2)
        for pull_request in pull_requests:
            self.assertGreaterEqual(pull_request.id, 670)

    def test_get_pull_request_source_branch_name(self):
        pr_source_branch_name = self.git.get_pull_request_source_branch_name('MVAS', 'uvuddb', '670')
        self.assertEqual(pr_source_branch_name, 'hotfix/12.1.1.HF6')

    def test_get_pull_request_destination_branch_name(self):
        pr_destination_branch_name = self.git.get_pull_request_destination_branch_name('MVAS', 'uvuddb', '670')
        self.assertEqual(pr_destination_branch_name, 'uv1212-dev')

    def test_get_pull_request_relate_jira_key(self):
        relate_jira_key = self.git.get_pull_request_relate_jira_key('MVAS', 'uvuddb', '671')
        self.assertEqual(relate_jira_key, 'UNV-30005')

    def test_get_pull_request_id(self):
        pr_ids = self.git.get_pull_request_id('MVAS', 'uvuddb', pr_state="MERGED", limit=0)
        for pr_id in pr_ids:
            self.assertGreaterEqual(pr_id, 671)

    def test_get_the_pull_request_diff(self):
        pr_diff = self.git.get_pull_request_diff('MVAS', 'uvuddb', 671)
        self.assertEqual(pr_diff.fromHash, 'dad7e0380d6e665bfda907da8eec38e383994224')
        self.assertEqual(pr_diff.toHash, 'e2e805087195616f43b1458472c6ecbf5264b180')

    def test_add_delete_comment_to_pull_request(self):
        # self.git.add_comment_to_pull_request('MVAS', 'uvuddb', 585, 'Add comment by rest api.')
        comment_values = self.git.get_pull_request_activities('MVAS', 'uvuddb', 585)
        comments = []
        for comment_value in comment_values:
            try:
                comments.append(comment_value.comment.text)
            except AttributeError:
                pass
        self.assertIn('Add comment by rest api.', comments)
        self.git.remove_comment_from_pull_request('MVAS', 'uvuddb', 585, 'Add comment by rest api.')

    def test_get_file_change_history(self):
        history = self.git.get_file_change_history(
            'MVAS', 'uvuddb', 'release/12.1.1.HF6.PE', 'src/uv/uvsrc/port.note', limit=0)
        self.assertEqual(len(history), 1)

    def test_get_file_content(self):
        file_content = self.git.get_file_content('MVAS', 'uvuddb', 'release/12.1.1.HF6.PE', '.gitignore')
        self.assertIn('# windows ignorance files', file_content)

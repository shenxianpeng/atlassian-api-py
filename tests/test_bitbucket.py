import unittest
import configparser
from atlassian import Bitbucket

config = configparser.ConfigParser()
config.read('config.ini')

git_url = config['bitbucket']['url']
git_usr = config['bitbucket']['username']
api_key = config['bitbucket']['password']


class TestJira(unittest.TestCase):

    def setUp(self):
        # https://shenxianpeng.atlassian.net/rest/api/2/issue/AAP-1
        self.git = Bitbucket(url=git_url, username=git_usr, password=api_key)

    def test_get_project_repo(self):
        repos = self.git.get_project_repo('MVAS')
        print(repos)




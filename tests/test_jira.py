import unittest
import configparser
from atlassian import Jira

config = configparser.ConfigParser()
config.read('../atlassian/config.ini')

jira_url = config['jira']['url']
jira_usr = config['jira']['username']
jira_psw = config['jira']['password']


class TestJira(unittest.TestCase):

    def setUp(self):
        self.jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)

    def test_get_status(self):
        status = self.jira.get_issue_status('MVQA-1')
        self.assertEqual(status, 'Closed')

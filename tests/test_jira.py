import unittest
import configparser
from atlassian import Jira

config = configparser.ConfigParser()
config.read('config.ini')

jira_url = config['jira']['url']
jira_usr = config['jira']['username']
password = config['jira']['password']


class TestJira(unittest.TestCase):

    def setUp(self):
        # https://jira.rocketsoftware.com/browse/MVQA-900
        self.jira = Jira(url=jira_url, username=jira_usr, password=password)

    def test_issue(self):
        issue = self.jira.issue('MVQA-900')
        self.assertEqual(issue.id, '1684517')
        self.assertEqual(issue.key, 'MVQA-900')
        self.assertEqual(issue.fields.assignee.key, 'xshen')
        self.assertEqual(issue.fields.status.name, 'Triage')
        self.assertEqual(issue.fields.issuetype.name, 'Bug')
        self.assertGreaterEqual(len(issue.fields.subtasks), 7, "There are more then 7 sub-tasks exist")
        self.assertEqual(issue.fields.summary, 'Jira REST API Unit Test Example')
        self.assertEqual(issue.fields.fixVersions[0].name, '2019')
        self.assertEqual(issue.fields.components[0].name, 'Test automation')
        self.assertGreaterEqual(len(issue.fields.attachment), 2)
        self.assertEqual(issue.fields.labels, ['AddLabel', 'Test'])
        self.assertEqual(issue.fields.customfield_17533, ['AddLabel', 'Test'])

    def test_update_issue_description(self):
        self.jira.update_issue_description('MVQA-900', 'update description')
        description = self.jira.get_issue_description('MVQA-900')
        self.assertEqual(description, 'update description')

        self.jira.update_issue_description('MVQA-900', 'This is a test example, please DO NOT modify.')
        description = self.jira.get_issue_description('MVQA-900')
        self.assertEqual(description, 'This is a test example, please DO NOT modify.')

    def test_add_delete_issue_comment(self):
        self.jira.add_issue_comment('MVQA-900', "Add comment by REST API.")
        comments = self.jira.get_issue_comments('MVQA-900')
        for comment in comments:
            if comment['body'] == 'Add comment by REST API.':
                comment_id = comment['id']
        self.jira.delete_issue_comment('MVQA-900', comment_id)

    def test_search_issue_with_sql(self):
        sql = 'project = "MVQA" and issuekey=MVQA-900 ORDER BY created DESC'
        result = self.jira.search_issue_with_sql(sql)
        self.assertEqual(result['total'], 1)

    def test_get_user(self):
        username = self.jira.get_user('xshen')
        self.assertEqual(username['key'], 'xshen')

    def test_get_user_active(self):
        active_status = self.jira.get_user_active('bklein')
        self.assertEqual(active_status, False)

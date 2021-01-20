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

    def test_get_issue_id(self):
        issue_id = self.jira.get_issue_id('MVQA-900')
        self.assertEqual(issue_id, '1684517')

    def test_get_status(self):
        status = self.jira.get_issue_status('MVQA-900')
        self.assertEqual(status, 'Triage')

    def test_get_sub_tasks_under_jira(self):
        sub_tasks = self.jira.get_sub_tasks_under_jira('MVQA-900')
        self.assertGreaterEqual(len(sub_tasks), 7, "There are more then 7 sub-tasks exist")

    def test_issue_summary(self):
        summary = self.jira.get_issue_summary('MVQA-900')
        self.assertEqual(summary, 'Jira REST API Unit Test Example')

    def test_get_issue_fix_versions_name(self):
        fix_version = self.jira.get_issue_fix_versions_name('MVQA-900')
        self.assertEqual(fix_version, ['2019'])

    def test_get_issue_component(self):
        component = self.jira.get_issue_component('MVQA-900')
        self.assertEqual(component, ['Test automation'])

    def test_get_issue_label(self):
        label = self.jira.get_issue_label('MVQA-900')
        self.assertIn('Test', label)

    def test_update_issue_label(self):
        self.jira.update_issue_label('MVQA-900', remove_labels=['Test'], add_labels=['Test', 'AddLabel'])
        label = self.jira.get_issue_label('MVQA-900')
        self.assertEqual(label, ['AddLabel', 'Test'])

    def test_get_issue_links(self):
        issue_links = self.jira.get_issue_links('MVQA-900')
        issue_keys = []
        for issue_link in issue_links:
            issue_key = issue_link['outwardIssue']['key']
            issue_keys.append(issue_key)
        self.assertIn('MVQA-904', issue_keys)

    def test_get_issue_description(self):
        description = self.jira.get_issue_description('MVQA-900')
        self.assertEqual(description, 'This is a test example, please DO NOT modify.')

    def test_update_issue_description(self):
        self.jira.update_issue_description('MVQA-900', 'update description')
        description = self.jira.get_issue_description('MVQA-900')
        self.assertEqual(description, 'update description')

        self.jira.update_issue_description('MVQA-900', 'This is a test example, please DO NOT modify.')
        description = self.jira.get_issue_description('MVQA-900')
        self.assertEqual(description, 'This is a test example, please DO NOT modify.')

    def test_get_issue_assignee_key(self):
        assignee_key = self.jira.get_issue_assignee_key('MVQA-900')
        self.assertEqual(assignee_key, 'xshen')

    def test_get_issue_assignee_name(self):
        assignee_name = self.jira.get_issue_assignee_name('MVQA-900')
        self.assertEqual(assignee_name, 'Xianpeng Shen')

    def test_get_issue_comments(self):
        comments = self.jira.get_issue_comments('MVQA-900')
        comments_body = []
        for comment in comments:
            comments_body.append(comment['body'])
        self.assertIn('Please don’t do any changes to this ticket. thanks!', comments_body)

    def test_add_delete_issue_comment(self):
        self.jira.add_issue_comment('MVQA-900', "Add comment by REST API.")
        comments = self.jira.get_issue_comments('MVQA-900')
        for comment in comments:
            if comment['body'] == 'Add comment by REST API.':
                comment_id = comment['id']
        self.jira.delete_issue_comment('MVQA-900', comment_id)

    def test_get_last_n_comment(self):
        comment = self.jira.get_last_n_comment('MVQA-900', last_n=1)
        self.assertIn('Please don’t do any changes to this ticket. thanks!', comment['body'])

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

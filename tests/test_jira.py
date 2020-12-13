import unittest
import configparser
from atlassian import Jira

config = configparser.ConfigParser()
config.read('config.ini')

jira_url = config['jira']['url']
jira_usr = config['jira']['username']
api_key = config['jira']['password']


class TestJira(unittest.TestCase):

    def setUp(self):
        # https://shenxianpeng.atlassian.net/rest/api/2/issue/AAP-1
        self.jira = Jira(url=jira_url, username=jira_usr, password=api_key)

    def test_get_issue_id(self):
        issue_id = self.jira.get_issue_id('AAP-1')
        self.assertEqual(issue_id, '10000')

    def test_get_status(self):
        status = self.jira.get_issue_status('AAP-1')
        self.assertEqual(status, 'Backlog')

    def test_get_sub_tasks_under_jira(self):
        sub_tasks = self.jira.get_sub_tasks_under_jira('AAP-1')
        self.assertEqual(len(sub_tasks), 2, "There are two sub-tasks exist")

    def test_issue_summary(self):
        summary = self.jira.get_issue_summary('AAP-1')
        self.assertEqual(summary, 'Unit Test Example')

    def test_get_issue_fix_versions_name(self):
        fix_version = self.jira.get_issue_fix_versions_name('AAP-1')
        self.assertEqual(fix_version, ['0.1.0'])

    # TODO
    # def test_get_issue_component(self):
    #     component = self.jira.get_issue_component('AAP-1')
    #     self.assertEqual(component, ['unittest'])

    def test_get_issue_label(self):
        label = self.jira.get_issue_label('AAP-1')
        self.assertIn('Test', label)

    def test_update_issue_label(self):
        self.jira.update_issue_label('AAP-1', remove_labels=['Test'], add_labels=['Test', 'AddLabel'])
        label = self.jira.get_issue_label('AAP-1')
        self.assertEqual(label, ['AddLabel', 'Test'])

    def test_get_issue_links(self):
        issue_links = self.jira.get_issue_links('AAP-1')
        issue_keys = []
        for issue_link in issue_links:
            issue_key = issue_link['inwardIssue']['key']
            issue_keys.append(issue_key)
        self.assertIn('AAP-4', issue_keys)

    def test_get_issue_description(self):
        description = self.jira.get_issue_description('AAP-1')
        self.assertEqual(description, 'This is a test example')

    def test_update_issue_description(self):
        self.jira.update_issue_description('AAP-1', 'update description')
        description = self.jira.get_issue_description('AAP-1')
        self.assertEqual(description, 'update description')

        self.jira.update_issue_description('AAP-1', 'This is a test example')
        description = self.jira.get_issue_description('AAP-1')
        self.assertEqual(description, 'This is a test example')

    def test_get_issue_assignee_key(self):
        assignee_key = self.jira.get_issue_assignee_key('AAP-1')
        self.assertEqual(assignee_key, {})

    def test_get_issue_assignee_name(self):
        assignee_name = self.jira.get_issue_assignee_name('AAP-1')
        self.assertEqual(assignee_name, 'shen xianpeng')

    def test_get_issue_comments(self):
        comments = self.jira.get_issue_comments('AAP-1')
        comments_body = []
        for comment in comments:
            comments_body.append(comment['body'])
        self.assertIn('Please don’t do any changes to this ticket. thanks\!', comments_body)

    def test_add_delete_issue_comment(self):
        self.jira.add_issue_comment('AAP-1', "Add comment by REST API.")
        comments = self.jira.get_issue_comments('AAP-1')
        for comment in comments:
            if comment['body'] == 'Add comment by REST API.':
                comment_id = comment['id']
        self.jira.delete_issue_comment('AAP-1', comment_id)

    def test_get_last_n_comment(self):
        comment = self.jira.get_last_n_comment('AAP-1', last_n=1)
        self.assertIn('Please don’t do any changes to this ticket. thanks\!', comment['body'])

    def test_search_issue_with_sql(self):
        sql = 'project = "AAP" and issuekey=AAP-1 ORDER BY created DESC'
        result = self.jira.search_issue_with_sql(sql)
        self.assertEqual(result['total'], 1)




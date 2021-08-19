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
        self.jira = Jira(url=jira_url, username=jira_usr, password=password)
        self.issue = self.jira.issue('MVQA-900')

    def test_issue(self):
        self.assertEqual(self.issue.id, '1684517')
        self.assertEqual(self.issue.key, 'MVQA-900')
        self.assertEqual(self.issue.fields.assignee.key, 'xshen')
        self.assertEqual(self.issue.fields.status.name, 'Triage')
        self.assertEqual(self.issue.fields.issuetype.name, 'Bug')
        self.assertGreaterEqual(len(self.issue.fields.subtasks), 7, "There are more then 7 sub-tasks exist")
        self.assertEqual(self.issue.fields.summary, 'Jira REST API Unit Test Example')
        self.assertEqual(self.issue.fields.fixVersions[0].name, '2019')
        self.assertEqual(self.issue.fields.components[0].name, 'Test automation')
        self.assertGreaterEqual(len(self.issue.fields.attachment), 2)

    def test_update_issue_label(self):
        labels = ['AddLabel', 'Test']
        self.jira.update_issue_label(issue_key='MVQA-900', add_labels=labels)
        issue = self.jira.issue('MVQA-900')
        self.assertEqual(issue.fields.labels, labels)
        self.jira.update_issue_label(issue_key='MVQA-900', remove_labels=labels)

    def test_update_issue_component(self):
        components = ['UDT', 'UNV', 'UNDK']
        self.jira.update_issue_component(issue_key='MVQA-900', add_components=components)
        self.jira.update_issue_component(issue_key='MVQA-900', remove_components=components)

    def test_update_custom_field_owner(self):
        """Update Jira project owner"""
        field_id = 'customfield_11386'
        field_key = 'name'
        field_value = 'xshen'
        self.jira.update_custom_field('LINF-4', field_id, field_key, field_value)
        issue = self.jira.issue('LINF-4')
        self.assertEqual(issue.fields.customfield_11386.name, 'xshen')

    def test_update_custom_field_solution(self):
        field_id = 'customfield_10985'
        field_value = 'Update Solution - 3'
        self.jira.update_custom_field('UNV-31074', field_id, field_value)

    def test_update_issue_description(self):
        self.jira.update_issue_description('MVQA-900', 'update description')
        issue = self.jira.issue('MVQA-900')
        description = issue.fields.description
        self.assertEqual(description, 'update description')

        self.jira.update_issue_description('MVQA-900', 'This is a test example, please DO NOT modify.')
        issue = self.jira.issue('MVQA-900')
        description = issue.fields.description
        self.assertEqual(description, 'This is a test example, please DO NOT modify.')

    def test_add_delete_issue_comment(self):
        self.jira.add_issue_comment('MVQA-900', "Add comment by REST API.")
        issue = self.jira.issue('MVQA-900')
        comments = issue.fields.comment.comments
        for comment in comments:
            if comment.body == 'Add comment by REST API.':
                self.jira.delete_issue_comment('MVQA-900', comment.id)

    def test_issue_transition(self):
        self.jira.issue_transition('LINF-4', transition_id=51)  # Close issue
        issue = self.jira.issue('LINF-4')
        self.assertEqual('Closed', issue.fields.status.name)
        self.jira.issue_transition('LINF-4', transition_id=61)  # Open issue
        issue = self.jira.issue('LINF-4')
        self.assertEqual('Open', issue.fields.status.name)

    def test_search_issue_with_sql(self):
        sql = 'project = MVQA ORDER BY priority DESC, updated DESC'
        result = self.jira.search_issue_with_sql(sql, max_result=2000)
        self.assertEqual(len(result['issues']), 1000)

    def test_get_project_components(self):
        results = self.jira.get_project_components("LINF")
        component_name_list = []
        for result in results:
            component_name_list.append(result.name)
        self.assertIn("Large", component_name_list)

    def test_user(self):
        username = self.jira.user('xshen')
        self.assertEqual(username.key, 'xshen')

    def test_user_active(self):
        username = self.jira.user('bklein')
        self.assertEqual(username.active, False)

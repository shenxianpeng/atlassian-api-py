import unittest
from atlassian import Jira

jira_url = os.getenv('JIRA_URL')
jira_usr = os.getenv('JIRA_USR')
jira_psw = os.getenv('JIRA_PSW')


class TestJira(unittest.TestCase):
    """Jira Test Cases"""

    def setUp(self):
        """Set connect with Jira instance"""
        self.jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)
        self.issue = self.jira.issue("MVQA-900")

    def test_issue(self):
        """Test to get issue information"""
        self.assertEqual(self.issue.id, "1684517")
        self.assertEqual(self.issue.key, "MVQA-900")
        self.assertEqual(self.issue.fields.assignee.key, "xshen")
        self.assertEqual(self.issue.fields.status.name, "Triage")
        self.assertEqual(self.issue.fields.issuetype.name, "Bug")
        self.assertGreaterEqual(
            len(self.issue.fields.subtasks), 7, "There are more then 7 sub-tasks exist"
        )
        self.assertEqual(self.issue.fields.summary, "Jira REST API Unit Test Example")
        self.assertEqual(self.issue.fields.fixVersions[0].name, "2019")
        self.assertEqual(self.issue.fields.components[0].name, "Test automation")
        self.assertGreaterEqual(len(self.issue.fields.attachment), 2)

    def test_issue_changelog(self):
        """Test to get issue changelog"""
        result = self.jira.issue_changelog("MVQA-900")
        histories = result.changelog.histories
        self.assertGreaterEqual(len(histories), 93)

    def test_update_issue_label(self):
        """Test to update issue label"""
        labels = ["AddLabel", "Test"]
        self.jira.update_issue_label(issue_key="MVQA-900", add_labels=labels)
        issue = self.jira.issue("MVQA-900")
        self.assertEqual(issue.fields.labels, labels)
        self.jira.update_issue_label(issue_key="MVQA-900", remove_labels=labels)

    def test_update_issue_component(self):
        """Test to update issue component"""
        components = ["UDT", "UNV", "UNDK"]
        self.jira.update_issue_component(
            issue_key="MVQA-900", add_components=components
        )
        self.jira.update_issue_component(
            issue_key="MVQA-900", remove_components=components
        )

    def test_update_field(self):
        """Test to update issue field"""
        self.jira.update_field("MVQA-900", "fixVersions", add="2019", remove="2017Q2")
        self.jira.update_field("MVQA-900", "versions", add="2019", remove="2017Q2")

    def test_update_custom_field_owner(self):
        """Test to update issue's custome field of owner"""
        field_id = "customfield_11386"
        field_key = "name"
        field_value = "xshen"
        self.jira.update_custom_field("LINF-4", field_id, field_key, field_value)
        issue = self.jira.issue("LINF-4")
        self.assertEqual(issue.fields.customfield_11386.name, "xshen")

    def test_update_custom_field_solution(self):
        """Test to update issue's custom field of solution"""
        field_id = "customfield_10985"
        field_value = "Update Solution - 3"
        self.jira.update_custom_field("UNV-31074", field_id, field_value)

    def test_update_issue_description(self):
        """Test to update issue description"""
        self.jira.update_issue_description("MVQA-900", "update description")
        issue = self.jira.issue("MVQA-900")
        description = issue.fields.description
        self.assertEqual(description, "update description")

        self.jira.update_issue_description(
            "MVQA-900", "This is a test example, please DO NOT modify."
        )
        issue = self.jira.issue("MVQA-900")
        description = issue.fields.description
        self.assertEqual(description, "This is a test example, please DO NOT modify.")

    def test_add_delete_issue_comment(self):
        """Test to add and remove comment of issue"""
        self.jira.add_issue_comment("MVQA-900", "Add comment by REST API.")
        issue = self.jira.issue("MVQA-900")
        comments = issue.fields.comment.comments
        for comment in comments:
            if comment.body == "Add comment by REST API.":
                self.jira.delete_issue_comment("MVQA-900", comment.id)

    @unittest.skip  # skip this one as it will create jira issue
    def test_create_issue(self):
        """Test to create issue"""
        data = {
            "project": {"key": "MVQA"},
            "assignee": {"name": "xshen"},
            "issuetype": {"name": "Task"},
            "summary": "Test create issue",
            "description": "test rest api",
        }
        self.jira.create_issue(fields=data)

    def test_issue_transition(self):
        """Test to do issue transition"""
        self.jira.issue_transition("LINF-4", transition_id=51)  # Close issue
        issue = self.jira.issue("LINF-4")
        self.assertEqual("Closed", issue.fields.status.name)
        self.jira.issue_transition("LINF-4", transition_id=61)  # Open issue
        issue = self.jira.issue("LINF-4")
        self.assertEqual("Open", issue.fields.status.name)

    def test_get_transitions(self):
        """Test to get issue transitions infromation"""
        result = self.jira.get_transitions("MVQA-900")
        transitions = result.transitions
        transition_names = []
        for transition in transitions:
            name = transition.name
            transition_names.append(name)
        self.assertIn("Accept to Backlog", transition_names)

    def test_search_issue_with_jql(self):
        """Test to search issue with JQL"""
        jql = "project = MVQA ORDER BY priority DESC, updated DESC"
        result = self.jira.search_issue_with_jql(jql, max_result=2000)
        self.assertEqual(len(result["issues"]), 1000)

    def test_get_project_components(self):
        """Test to get project components"""
        results = self.jira.get_project_components("LINF")
        component_name_list = []
        for result in results:
            component_name_list.append(result.name)
        self.assertIn("Large", component_name_list)

    def test_user(self):
        """Test to get uesr information"""
        username = self.jira.user("xshen")
        self.assertEqual(username.key, "xshen")

    def test_user_active(self):
        """Test user active or inactive"""
        username = self.jira.user("bklein")
        self.assertEqual(username.active, False)

    def test_get_dev_status(self):
        """Test to get dev status"""
        issue = self.jira.issue("MVQA-827")
        issue_id = issue.id
        dev_status = self.jira.get_dev_status(issue_id)
        self.assertEqual(dev_status.detail[0].repositories[0].name, "u2cicd")

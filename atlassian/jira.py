import configparser
from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """
    JIRA API Reference
    https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/
    """

    def get_id(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}".format(issue_key=issue_key)
        return (self.get(url) or {}).get("id") or {}

    def get_status(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=status".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("status") or {}).get("name") or {}

    def get_component(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=components".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("components") or {}).get("name") or {}

    def get_test_automation_status(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=customfield_17533".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("customfield_17533") or {}).get("value") or {}

    def get_issue_links(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=issuelinks".format(issue_key=issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get("issuelinks") or {}

    def get_issue_assignee_key(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=assignee".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("assignee") or {}).get("key") or {}

    def get_issue_assignee_name(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=assignee".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("assignee") or {}).get("displayName") or {}

    def get_comments(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}/comment".format(issue_key=issue_key)
        return (self.get(url) or {}).get("comments") or {}

    def add_comments(self, issue_key, content=None):
        url = "/rest/api/2/issue/{issue_key}/comment".format(issue_key=issue_key)
        json = {"body": content}
        return self.post(url, json=json) or {}

    def get_last_n_comment(self, issue_key, last_n=1):
        comments = self.get_comments(issue_key)
        try:
            return comments[len(comments)-last_n] or {}
        except IndexError as e:
            logger.error(e)

    def delete_comment(self, issue_key, comment_id):
        url = "/rest/api/2/issue/{issue_key}/comment/{comment_id}".format(issue_key=issue_key, comment_id=comment_id)
        return self.delete(url) or None

    def link_issue_as(self, type_name=None, inward_issue=None, outward_issue=None):
        """
        Link issue as depends_upon, is_blocked_by, etc.
        Example: jira.link_issue_as(type_name='Dependence', inward_issue="TEST-1", outward_issue='TEST-2')
        :param type_name: Dependence, Blocking
        :param inward_issue:
        :param outward_issue:
        :return:
        """
        url = '/rest/api/2/issueLink'
        json = {
            "type": {"name": type_name},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue}
        }
        return self.post(url, json=json)

    def delete_issue_link(self, link_id):
        url = '/rest/api/2/issueLink/{link_id}'.format(link_id=link_id)
        return self.delete(url) or {}

    def create_sub_task(self,
                        project_key=None,
                        parent_issue_key=None,
                        summary=None,
                        fix_version=None,
                        assignee=None,
                        description=None,
                        team=None):
        url = '/rest/api/2/issue'
        json = {
            "fields": {
                "project": {"key": project_key},
                "parent": {"key": parent_issue_key},
                "summary": summary,
                "issuetype": {"id": "20"},
                "assignee": {"key": assignee, "name": assignee},
                "priority": {"id": "4"},
                "description": description,
                "customfield_13430": {"value": "Testing / Debugging"},
                "customfield_11360": {"value": team},
                "fixVersions": [{"name": fix_version}]
            }
        }
        return self.post(url, json=json)

    def search_with_sql(self, jql, max_result=25):
        url = '/rest/api/2/search'
        json = {
            "jql": jql,
            "startAt": 0,
            "maxResults": max_result,
            "fields": [
                "summary",
                "status",
                "issuetype",
                "fixVersions"
            ]
        }
        return self.post(url, json=json) or {}


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    jira_url = config['jira']['url']
    jira_usr = config['jira']['username']
    jira_psw = config['jira']['password']

    jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)
    comment = jira.link_issue_as(type_name='Dependence', inward_issue="MVQA-900", outward_issue='MVQA-904')


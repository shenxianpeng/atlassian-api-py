from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """
    JIRA API Reference
    https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/
    """

    def get_issue_id(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}".format(issue_key=issue_key)
        return (self.get(url) or {}).get("id") or {}

    def get_issue_status(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=status".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("status") or {}).get("name") or {}

    def get_issue_type(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=issuetype".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("issuetype") or {}).get("name") or {}

    def get_sub_tasks_under_jira(self, issue_key):
        url = '/rest/api/2/issue/{issue_key}'.format(issue_key=issue_key)
        return ((self.get(url) or {}).get('fields') or {}).get("subtasks") or {}

    def get_issue_summary(self, issue_key):
        url = '/rest/api/2/issue/{issue_key}?fields=summary'.format(issue_key=issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get("summary") or {}

    def get_issue_fix_versions_name(self, issue_key):
        url = '/rest/api/2/issue/{issue_key}?fields=fixVersions'.format(issue_key=issue_key)
        fix_versions_name = []
        results = ((self.get(url) or {}).get("fields") or {}).get("fixVersions")
        for result in results:
            fix_versions_name.append(result['name'])
        return fix_versions_name

    def get_issue_component(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=components".format(issue_key=issue_key)
        results = ((self.get(url) or {}).get("fields") or {}).get("components") or {}
        components_name = []
        for result in results:
            components_name.append(result['name'])
        return components_name

    def get_issue_attachment(self, issue_key):
        url = '/rest/api/2/issue/{issue_key}?fields=attachment'.format(issue_key=issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get("attachment") or {}

    def get_issue_attachment_download_url(self, issue_key):
        attachments = self.get_issue_attachment(issue_key)
        download_url = []
        for attachment in attachments:
            download_url.append(attachment['content'])
        return download_url

    def get_issue_label(self, issue_key):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get('labels') or {}

    def update_issue_label(self, issue_key, remove_labels=None, add_labels=None):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        add_labels_list = []
        remove_labels_list = []
        if add_labels is not None:
            for add_label in add_labels:
                add_temp = {"add": add_label}
                add_labels_list.append(add_temp)

        if remove_labels is not None:
            for remove_label in remove_labels:
                remove_temp = {"remove": remove_label}
                remove_labels_list.append(remove_temp)

        if add_labels and remove_labels:
            json = {"update": {"labels": remove_labels_list + add_labels_list}}
        elif add_labels:
            json = {"update": {"labels": add_labels_list}}
        elif remove_labels:
            json = {"update": {"labels": remove_labels_list}}
        return self.put(url, json=json)

    def get_issue_test_automation_status(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=customfield_17533".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("customfield_17533") or {}).get("value") or {}

    def get_issue_links(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=issuelinks".format(issue_key=issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get("issuelinks") or {}

    def get_issue_description(self, issue_key):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        return ((self.get(url) or {}).get("fields") or {}).get("description") or {}

    def update_issue_description(self, issue_key, new_description):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        json = {"fields": {"description": new_description}}
        return self.put(url, json=json)

    def get_issue_assignee_key(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=assignee".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("assignee") or {}).get("key") or {}

    def get_issue_assignee_name(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}?fields=assignee".format(issue_key=issue_key)
        return (((self.get(url) or {}).get("fields") or {}).get("assignee") or {}).get("displayName") or {}

    def get_issue_comments(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}/comment".format(issue_key=issue_key)
        return (self.get(url) or {}).get("comments") or {}

    def add_issue_comment(self, issue_key, content=None):
        url = "/rest/api/2/issue/{issue_key}/comment".format(issue_key=issue_key)
        json = {"body": content}
        return self.post(url, json=json) or {}

    def get_issue_comments_body(self, issue_key, last_n=None):
        comments_dict = self.get_issue_comments(issue_key)
        index = len(comments_dict)
        comments_body = []
        if last_n is not None:
            if index >= last_n:
                index = last_n
        while index:
            comments_body.append(comments_dict[index-1]['body'])
            index = index-1
        return comments_body

    def get_last_n_comment(self, issue_key, last_n=1):
        comments = self.get_issue_comments(issue_key)
        try:
            return comments[len(comments)-last_n] or {}
        except IndexError as e:
            logger.error(e)

    def delete_issue_comment(self, issue_key, comment_id):
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
                        labels=None,
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
                "labels": labels,
                "customfield_13430": {"value": "Testing / Debugging"},
                "customfield_11360": {"value": team},
                "fixVersions": [{"name": fix_version}]
            }
        }
        if team is None:
            del json["fields"]['customfield_11360']

        return self.post(url, json=json)

    def assign_issue(self, issue_key, assignee=None):
        url = '/rest/api/2/issue/{0}/assignee'.format(issue_key)
        if assignee is None:
            assignee = -1
        json = {"name": assignee}
        return self.put(url, json=json) or {}

    def add_issue_watcher(self, issue_key, watcher):
        url = '/rest/api/2/issue/{0}/watchers'.format(issue_key)
        return self.post(url, json=watcher)

    def close_issue(self, issue_key, comment):
        url = '/rest/api/2/issue/{0}/transitions'.format(issue_key)
        json = {
            "update": {
                "comment": [
                    {
                        "add": {
                            "body": comment
                        }
                    }
                ]
            },
            "fields": {
                "resolution": {
                    "name": "Fixed/Completed"
                }
            },
            "customfield_13430": {
                "value": "null"
            },
            "transition": {
                "id": "31"
            }
        }
        return self.post(url, json=json)

    def reopen_issue(self, issue_key, comment):
        url = '/rest/api/2/issue/{0}/transitions'.format(issue_key)
        json = {
            "update": {"comment": [{"add": {"body": comment}}]},
            "transition": {"id": "41"}
        }
        return self.post(url, json=json)

    def search_issue_with_sql(self, jql, max_result=25):
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

    def get_user(self, username):
        url = '/rest/api/2/user?username={0}'.format(username)
        return self.get(url) or {}

    def get_user_active(self, username):
        url = '/rest/api/2/user?username={0}'.format(username)
        return (self.get(url) or {}).get("active")


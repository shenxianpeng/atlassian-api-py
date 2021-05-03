from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """
    JIRA API Reference
    https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/
    """

    def issue(self, issue_key):
        url = "/rest/api/2/issue/{issue_key}".format(issue_key=issue_key)
        return self.get(url) or {}

    def update_issue_label(self, issue_key, add_labels=None, remove_labels=None):
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
        label_data = {}
        if add_labels and remove_labels:
            label_data = {"update": {"labels": remove_labels_list + add_labels_list}}
        elif add_labels:
            label_data = {"update": {"labels": add_labels_list}}
        elif remove_labels:
            label_data = {"update": {"labels": remove_labels_list}}
        return self.put(url, json=label_data)

    def update_issue_component(self, issue_key, add_components=None, remove_components=None):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        add_component_list = []
        remove_component_list = []
        if add_components is not None:
            for add_component in add_components:
                add_temp = {"add": {"name": add_component}}
                add_component_list.append(add_temp)
        if remove_components is not None:
            for remove_component in remove_components:
                remove_temp = {"remove": {"name": remove_component}}
                remove_component_list.append(remove_temp)
        component_data = {}
        if add_components and remove_components:
            component_data = {"update": {"components": add_component_list + remove_component_list}}
        elif add_components:
            component_data = {"update": {"components": add_component_list}}
        elif remove_components:
            component_data = {"update": {"components": remove_component_list}}
        return self.put(url, json=component_data)

    def update_issue_description(self, issue_key, new_description):
        url = '/rest/api/2/issue/{0}'.format(issue_key)
        json = {"fields": {"description": new_description}}
        return self.put(url, json=json)

    def add_issue_comment(self, issue_key, content=None):
        url = "/rest/api/2/issue/{issue_key}/comment".format(issue_key=issue_key)
        json = {"body": content}
        return self.post(url, json=json) or {}

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

    def create_task(self, project_key=None, summary=None, assignee=None, owner=None, labels=None, components=None,
                    issue_type=10):
        url = '/rest/api/2/issue'
        json = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"id": issue_type},
                "assignee": {"key": assignee, "name": assignee},
                "customfield_11386": {"key": owner, "name": owner},
                "priority": {"id": "4"},  # "name": "3 - Medium"
                "labels": labels,
                "components": components
            }
        }

        return self.post(url, json=json)

    def create_sub_task(self, project_key=None, parent_issue_key=None, summary=None, fix_version=None, assignee=None,
                        description=None, labels=None, team=None, issue_type=20):
        url = '/rest/api/2/issue'
        json = {
            "fields": {
                "project": {"key": project_key},
                "parent": {"key": parent_issue_key},
                "summary": summary,
                "issuetype": {"id": issue_type},
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

    def close_issue(self, issue_key):
        """ Each Jira project may have different id, in my project close id is 51.
        You can find the Close button in Jira, then right click on the view elements
        then find id="action_id_51", 51 is your close id."""
        url = '/rest/api/2/issue/{0}/transitions'.format(issue_key)
        json = {
            "transition": {
                "id": "51"
            }
        }
        return self.post(url, json=json)

    def reopen_issue(self, issue_key):
        """ Each Jira project may have different id, in my project open id is 61.
        You can find the Close button in Jira, then right click on the view elements
        then find id="action_id_61", 61 is your open id."""
        url = '/rest/api/2/issue/{0}/transitions'.format(issue_key)
        json = {
            "transition": {"id": "61"}
        }
        return self.post(url, json=json)

    # FIXME currently search with sql only support maxResults is 1000.
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

    def get_project_components(self, project_id):
        url = '/rest/api/2/project/{}/components'.format(project_id)
        return self.get(url) or {}

    def user(self, username):
        url = '/rest/api/2/user?username={0}'.format(username)
        return self.get(url) or {}

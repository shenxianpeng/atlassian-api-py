from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """
    JIRA API Reference
    https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/
    """

    def issue(self, issue_key):
        """Get issue fileds"""
        url = f"/rest/api/2/issue/{issue_key}"
        return self.get(url) or {}

    def issue_changelog(self, issue_key):
        """Get issue changelog"""
        # https://jira.atlassian.com/browse/JRASERVER-27692
        url = f"/rest/api/2/issue/{issue_key}?expand=changelog&fields=summary"
        return self.get(url) or {}

    def update_issue_label(self, issue_key, add_labels=None, remove_labels=None):
        """Update issue label"""
        url = f"/rest/api/2/issue/{issue_key}"
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

    def update_issue_component(
        self, issue_key, add_components=None, remove_components=None
    ):
        """Update issue components"""
        url = f"/rest/api/2/issue/{issue_key}"
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
            component_data = {
                "update": {"components": add_component_list + remove_component_list}
            }
        elif add_components:
            component_data = {"update": {"components": add_component_list}}
        elif remove_components:
            component_data = {"update": {"components": remove_component_list}}
        return self.put(url, json=component_data)

    def update_issue_description(self, issue_key, new_description):
        """Update issue description"""
        url = f"/rest/api/2/issue/{issue_key}"
        json = {"fields": {"description": new_description}}
        return self.put(url, json=json)

    def update_field(self, issue_key, field_name, add=None, remove=None):
        """Update issue field"""
        url = f"/rest/api/2/issue/{issue_key}"
        element = []
        if add:
            element.append({"add": {"name": add}})
        if remove:
            element.append({"remove": {"name": remove}})
        json = {"update": {field_name: element}}
        return self.put(url, json=json)

    def add_issue_comment(self, issue_key, content=None):
        """Add comment to issue"""
        url = f"/rest/api/2/issue/{issue_key}/comment"
        json = {"body": content}
        return self.post(url, json=json) or {}

    def delete_issue_comment(self, issue_key, comment_id):
        """Delete comment from issue"""
        url = f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
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
        url = "/rest/api/2/issueLink"
        json = {
            "type": {"name": type_name},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue},
        }
        return self.post(url, json=json)

    def delete_issue_link(self, link_id):
        """Delete link from issue"""
        url = f"/rest/api/2/issueLink/{link_id}"
        return self.delete(url) or {}

    def create_issue(self, fields, update=None):
        """
        Creates an issue or a sub-task from a JSON representation
        :param fields: JSON data
                mandatory keys are issuetype, summary and project
        :param update: JSON data
                Use it to link issues or update worklog
        :return:
            example:
                fields = dict(summary='Into The Night',
                              project = dict(key='APA'),
                              issuetype = dict(name='Story')
                              )
                update = dict(issuelinks={
                    "add": {
                        "type": {
                            "name": "Child-Issue"
                            },
                        "inwardIssue": {
                            "key": "ISSUE-KEY"
                            }
                        }
                    }
                )
                jira.create_issue(fields=fields, update=update)
        """
        url = "/rest/api/2/issue"
        data = {"fields": fields}
        if update:
            data["update"] = update
        return self.post(url, json=data)

    # TODO: replace by create_issue, will remove it in the future
    def create_task(
        self,
        project_key=None,
        summary=None,
        assignee=None,
        owner=None,
        labels=None,
        components=None,
        issue_type=10,
    ):
        """Create task issue"""
        url = "/rest/api/2/issue"
        json = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"id": issue_type},
                "assignee": {"key": assignee, "name": assignee},
                "customfield_11386": {"key": owner, "name": owner},
                "priority": {"id": "4"},  # "name": "3 - Medium"
                "labels": labels,
                "components": components,
            }
        }

        return self.post(url, json=json)

    # TODO: replace by create_issue, will remove it in the future
    def create_sub_task(
        self,
        project_key=None,
        parent_issue_key=None,
        summary=None,
        fix_version=None,
        assignee=None,
        description=None,
        labels=None,
        team=None,
        issue_type=20,
    ):
        """Create sub task issue"""
        url = "/rest/api/2/issue"
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
                "fixVersions": [{"name": fix_version}],
            }
        }
        if team is None:
            del json["fields"]["customfield_11360"]

        return self.post(url, json=json)

    def update_custom_field(self, issue_key, field_id, *field_args):
        """Update custom field. in my Jira project
        customfield_10985 is solution field which field_args length is 1
        customfield_11386 is owner field which field_args length is 2
        """
        url = f"/rest/api/2/issue/{issue_key}"
        if len(field_args) == 1:
            json = {"fields": {field_id: field_args[0]}}
        elif len(field_args) == 2:
            json = {"fields": {field_id: {field_args[0]: field_args[1]}}}
        else:
            raise AttributeError("Not support field_args length > 2")

        return self.put(url, json=json)

    def assign_issue(self, issue_key, assignee=None):
        """Assign issue to someone"""
        url = f"/rest/api/2/issue/{issue_key}/assignee"
        if assignee is None:
            assignee = -1
        json = {"name": assignee}
        return self.put(url, json=json) or {}

    def add_issue_watcher(self, issue_key, watcher):
        """Add someone as watcher"""
        url = f"/rest/api/2/issue/{issue_key}/watchers"
        return self.post(url, json=watcher)

    def issue_transition(self, issue_key, transition_id=None):
        """Each Jira project may have different transition_id. You can find your transition_id like below:
        Chose transition Button then right click on the view elements. for example:
        I find Close button's elements is id="action_id_51", so the close transition_id = 51.
        I find Open button's elements is id="action_id_61", so the open transition_id = 61.
        """
        url = "/rest/api/2/issue/{key}/transitions".format(key=issue_key)
        json = {"transition": {"id": transition_id}}
        return self.post(url, json=json)

    def get_transitions(self, issue_id):
        """Get a list of the transitions possible for this issue by the current user"""
        url = f"/rest/api/2/issue/{issue_id}/transitions"
        return self.get(url) or {}

    def search_issue_with_jql(self, jql, max_result=1000) -> list:
        url = "/rest/api/2/search"
        start_at = 0
        issues = []
        json = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_result,
            "fields": ["summary", "status", "issuetype", "fixVersions"],
        }
        response = self.post(url, json=json) or {}
        try:
            total = response["total"]
        except KeyError:
            return issues
        max_results = response["maxResults"]
        for issue in response["issues"]:
            issues.append(issue)

        while total > max_results:
            start_at = start_at + max_results
            json = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_result,
                "fields": ["summary", "status", "issuetype", "fixVersions"],
            }
            response = self.post(url, json=json) or {}
            total = total - max_results
            for issue in response["issues"]:
                issues.append(issue)
        return issues

    def get_project_components(self, project_id):
        """Get project components"""
        url = f"/rest/api/2/project/{project_id}/components"
        return self.get(url) or {}

    def user(self, username):
        """Get user information"""
        url = f"/rest/api/2/user?username={username}"
        return self.get(url) or {}

    def get_dev_status(self, issue_id, app_type="stash", data_type="repository"):
        """Get dev status"""
        url = f"/rest/dev-status/1.0/issue/detail?issueId={issue_id}&applicationType={app_type}&dataType={data_type}"
        return self.get(url) or {}

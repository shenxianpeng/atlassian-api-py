from __future__ import annotations

from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """
    JIRA API Reference

    .. seealso::
        `JIRA REST API Documentation <https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/>`_
    """

    def issue(self, issue_key: str) -> SimpleNamespace | str | None:
        """
        Get issue fields.

        :param issue_key: The key of the issue to retrieve.
        :type issue_key: str
        :return: A SimpleNamespace containing issue fields, a raw text response string, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        return self.get(url)

    def issue_changelog(self, issue_key: str) -> SimpleNamespace | str | None:
        """
        Get issue changelog.

        :param issue_key: The key of the issue to retrieve the changelog for.
        :type issue_key: str
        :return: A SimpleNamespace containing the issue changelog, a raw text response string, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}?expand=changelog&fields=summary"
        return self.get(url)

    def update_issue_label(
        self,
        issue_key: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict | None:
        """
        Update issue labels.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param add_labels: A list of labels to add.
        :type add_labels: list[str], optional
        :param remove_labels: A list of labels to remove.
        :type remove_labels: list[str], optional
        :return: The response from the API.
        :rtype: dict or None
        """
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
        self,
        issue_key: str,
        add_components: list[str] | None = None,
        remove_components: list[str] | None = None,
    ) -> dict | None:
        """
        Update issue components.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param add_components: A list of components to add.
        :type add_components: list[str], optional
        :param remove_components: A list of components to remove.
        :type remove_components: list[str], optional
        :return: The response from the API.
        :rtype: dict or None
        """
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

    def update_issue_description(
        self, issue_key: str, new_description: str
    ) -> dict | None:
        """
        Update issue description.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param new_description: The new description for the issue.
        :type new_description: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        json = {"fields": {"description": new_description}}
        return self.put(url, json=json)

    def update_field(
        self,
        issue_key: str,
        field_name: str,
        add: str | None = None,
        remove: str | None = None,
    ) -> dict | None:
        """
        Update a specific field of an issue.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param field_name: The name of the field to update.
        :type field_name: str
        :param add: The value to add to the field.
        :type add: str, optional
        :param remove: The value to remove from the field.
        :type remove: str, optional
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        element = []
        if add:
            element.append({"add": {"name": add}})
        if remove:
            element.append({"remove": {"name": remove}})
        json = {"update": {field_name: element}}
        return self.put(url, json=json)

    def add_issue_comment(
        self, issue_key: str, content: str | None = None
    ) -> dict | None:
        """
        Add a comment to an issue.

        :param issue_key: The key of the issue to add a comment to.
        :type issue_key: str
        :param content: The content of the comment.
        :type content: str, optional

        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment"
        json = {"body": content}
        return self.post(url, json=json)

    def delete_issue_comment(self, issue_key: str, comment_id: str) -> dict | None:
        """
        Delete a comment from an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param comment_id: The ID of the comment to delete.
        :type comment_id: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        return self.delete(url)

    def link_issue_as(
        self,
        type_name: str | None = None,
        inward_issue: str | None = None,
        outward_issue: str | None = None,
    ) -> dict | None:
        """
        Link two issues with a specific relationship.

        :param type_name: The type of the link (e.g., "Dependence", "Blocking").
        :type type_name: str, optional
        :param inward_issue: The key of the inward issue.
        :type inward_issue: str, optional
        :param outward_issue: The key of the outward issue.
        :type outward_issue: str, optional
        :return: The response from the API.
        :rtype: dict or None

        .. code-block:: python

            jira.link_issue_as(type_name='Dependence', inward_issue="TEST-1", outward_issue='TEST-2')
        """
        url = "/rest/api/2/issueLink"
        json = {
            "type": {"name": type_name},
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue},
        }
        return self.post(url, json=json)

    def delete_issue_link(self, link_id: str) -> dict | None:
        """Delete link from issue"""
        url = f"/rest/api/2/issueLink/{link_id}"
        return self.delete(url)

    def create_issue(self, fields: dict, update: dict | None = None) -> dict | None:
        """
        Creates an issue or a sub-task from a JSON representation.

        :param fields: JSON data. mandatory keys are issuetype, summary and project update: Use it to link issues or update worklog
        :type fields: dict

        :return: The response from the API.
        :rtype: dict or None
        """
        url = "/rest/api/2/issue"
        data = {"fields": fields}
        if update:
            data["update"] = update
        return self.post(url, json=data)

    # TODO: replace by create_issue, will remove it in the future
    def create_task(
        self,
        project_key: str | None = None,
        summary: str | None = None,
        assignee: str | None = None,
        owner: str | None = None,
        labels: list[str] | None = None,
        components: list[str] | None = None,
        issue_type: int = 10,
    ) -> dict | None:
        """
        Create task issue.

        :param project_key: The key of the project.
        :type project_key: str
        :param summary: The summary of the issue.
        :type summary: str
        :param assignee: The assignee of the issue.
        :type assignee: str
        :param owner: The owner of the issue.
        :type owner: str
        :param labels: A list of labels for the issue.
        :type labels: list[str], optional
        :param components: A list of components for the issue.
        :type components: list[str], optional
        :param issue_type: The issue type ID (default is 10).
        :type issue_type: int, optional
        :return: The response from the API.
        :rtype: dict or None
        """
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
        project_key: str | None = None,
        parent_issue_key: str | None = None,
        summary: str | None = None,
        fix_version: str | None = None,
        assignee: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        team: str | None = None,
        issue_type: int = 20,
    ) -> dict | None:
        """
        Create sub task issue.

        :param project_key: The key of the project.
        :type project_key: str
        :param parent_issue_key: The key of the parent issue.
        :type parent_issue_key: str
        :param summary: The summary of the issue.
        :type summary: str
        :param fix_version: The fix version of the issue.
        :type fix_version: str
        :param assignee: The assignee of the issue.
        :type assignee: str
        :param description: The description of the issue.
        :type description: str
        :param labels: A list of labels for the issue.
        :type labels: list[str], optional
        :param team: The team of the issue.
        :type team: str, optional
        :param issue_type: The issue type ID (default is 20).
        :type issue_type: int, optional
        :return: The response from the API.
        :rtype: dict or None
        """
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

    def update_custom_field(
        self, issue_key: str, field_id: str, *field_args: object
    ) -> dict | None:
        """
        Update custom field. in my Jira project.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param field_id: The ID of the custom field to update.
        :type field_id: str
        :param field_args: The new values for the custom field.
        :type field_args: tuple
        """
        url = f"/rest/api/2/issue/{issue_key}"
        if len(field_args) == 1:
            json = {"fields": {field_id: field_args[0]}}
        elif len(field_args) == 2:
            json = {"fields": {field_id: {field_args[0]: field_args[1]}}}
        else:
            raise AttributeError("Not support field_args length > 2")

        return self.put(url, json=json)

    def assign_issue(self, issue_key: str, assignee: str | None = None) -> dict | None:
        """
        Assign issue to someone.

        :param issue_key: The key of the issue to assign.
        :type issue_key: str
        :param assignee: The assignee of the issue.
        :type assignee: str, optional
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/assignee"
        # Pass -1 to unassign; JIRA API accepts either a username string or -1
        name: str | int = assignee if assignee is not None else -1
        json = {"name": name}
        return self.put(url, json=json)

    def add_issue_watcher(self, issue_key: str, watcher: str) -> dict | None:
        """
        Add someone as watcher.

        :param issue_key: The key of the issue to add a watcher to.
        :type issue_key: str
        :param watcher: The username of the watcher.
        :type watcher: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/watchers"
        # JIRA API expects the username as a raw JSON string body
        return self.post(url, json=watcher)  # type: ignore[arg-type]

    def issue_transition(
        self, issue_key: str, transition_id: str | None = None
    ) -> dict | None:
        """Each Jira project may have different transition_id. You can find your transition_id like below:
        Chose transition Button then right click on the view elements. for example:
        I find Close button's elements is id="action_id_51", so the close transition_id = 51.
        I find Open button's elements is id="action_id_61", so the open transition_id = 61.

        :param issue_key: The key of the issue to transition.
        :type issue_key: str
        :param transition_id: The ID of the transition to perform.
        :type transition_id: str, optional
        :return: The response from the API.
        :rtype: dict or None
        """
        url = "/rest/api/2/issue/{key}/transitions".format(key=issue_key)
        json = {"transition": {"id": transition_id}}
        return self.post(url, json=json)

    def get_transitions(self, issue_id: str) -> SimpleNamespace | str | None:
        """
        Get a list of the transitions possible for this issue by the current user.

        :param issue_id: The ID of the issue to get transitions for.
        :type issue_id: str
        :return: A SimpleNamespace containing the transitions.
        :rtype: SimpleNamespace or None
        """
        url = f"/rest/api/2/issue/{issue_id}/transitions"
        return self.get(url)

    def search_issue_with_jql(self, jql: str, max_result: int = 1000) -> list:
        """
        Search issues using JQL (JIRA Query Language).

        :param jql: The JQL query string.
        :type jql: str
        :param max_result: The maximum number of results to return (default is 1000).
        :type max_result: int, optional
        :return: A list of issues matching the JQL query.
        :rtype: list
        """
        url = "/rest/api/2/search"
        start_at = 0
        issues: list[str] = []
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

    def get_project_components(self, project_id: str) -> SimpleNamespace | str | None:
        """
        Get project components.

        :param project_id: The ID of the project to get components for.
        :type project_id: str
        :return: A SimpleNamespace containing the project components.
        :rtype: SimpleNamespace or None
        """
        url = f"/rest/api/2/project/{project_id}/components"
        return self.get(url)

    def user(self, username: str) -> SimpleNamespace | str | None:
        """
        Get user information by username.

        :param username: The username of the user to retrieve.
        :type username: str
        :return: A SimpleNamespace containing user information.
        :rtype: SimpleNamespace or None
        """
        url = f"/rest/api/2/user?username={username}"
        return self.get(url)

    def get_dev_status(
        self,
        issue_id: str,
        app_type: str = "stash",
        data_type: str = "repository",
    ) -> SimpleNamespace | str | None:
        """
        Get development status for an issue.

        :param issue_id: The ID of the issue to get development status for.
        :type issue_id: str
        :param app_type: The type of application (default is "stash").
        :type app_type: str, optional
        :param data_type: The type of data (default is "repository").
        :type data_type: str, optional
        :return: A SimpleNamespace containing the development status.
        :rtype: SimpleNamespace or None
        """
        url = f"/rest/dev-status/1.0/issue/detail?issueId={issue_id}&applicationType={app_type}&dataType={data_type}"
        return self.get(url)

    def delete_issue(self, issue_key: str) -> dict | None:
        """
        Delete an issue.

        :param issue_key: The key of the issue to delete.
        :type issue_key: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        return self.delete(url)

    def get_project(self, project_key: str) -> SimpleNamespace | str | None:
        """
        Get project information.

        :param project_key: The key of the project to retrieve.
        :type project_key: str
        :return: A SimpleNamespace containing project information.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/project/{project_key}"
        return self.get(url)

    def get_projects(self) -> SimpleNamespace | str | None:
        """
        Get all projects visible to the current user.

        :return: A SimpleNamespace containing all projects.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/2/project"
        return self.get(url)

    def get_issue_comments(self, issue_key: str) -> SimpleNamespace | str | None:
        """
        Get all comments for an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :return: A SimpleNamespace containing the comments.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment"
        return self.get(url)

    def update_issue_comment(
        self, issue_key: str, comment_id: str, content: str
    ) -> dict | None:
        """
        Update an existing comment on an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param comment_id: The ID of the comment to update.
        :type comment_id: str
        :param content: The new content of the comment.
        :type content: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        json = {"body": content}
        return self.put(url, json=json)

    def get_issue_watchers(self, issue_key: str) -> SimpleNamespace | str | None:
        """
        Get all watchers for an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :return: A SimpleNamespace containing the watchers.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}/watchers"
        return self.get(url)

    def get_versions(self, project_key: str) -> SimpleNamespace | str | None:
        """
        Get all versions for a project.

        :param project_key: The key of the project.
        :type project_key: str
        :return: A SimpleNamespace containing the project versions.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/project/{project_key}/versions"
        return self.get(url)

    def create_version(
        self,
        project_key: str,
        name: str,
        description: str | None = None,
        released: bool = False,
        start_date: str | None = None,
        release_date: str | None = None,
    ) -> dict | None:
        """
        Create a new version for a project.

        :param project_key: The key of the project.
        :type project_key: str
        :param name: The name of the version.
        :type name: str
        :param description: An optional description for the version.
        :type description: str, optional
        :param released: Whether the version has been released (default False).
        :type released: bool, optional
        :param start_date: The start date in YYYY-MM-DD format (optional).
        :type start_date: str, optional
        :param release_date: The release date in YYYY-MM-DD format (optional).
        :type release_date: str, optional
        :return: The response from the API.
        :rtype: dict or None
        """
        url = "/rest/api/2/version"
        payload: dict = {"project": project_key, "name": name, "released": released}
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["startDate"] = start_date
        if release_date is not None:
            payload["releaseDate"] = release_date
        return self.post(url, json=payload)

from __future__ import annotations

import warnings
from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """Client for Jira REST API operations.

    Use this class for issue lookup, issue updates, JQL searches, comments,
    watchers, transitions, projects, and versions. Responses from read methods
    are usually nested ``SimpleNamespace`` objects; methods that mutate Jira
    return decoded JSON dictionaries or ``None`` for empty responses.

    .. seealso::
        `Jira REST API Documentation <https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/>`_
    """

    def issue(self, issue_key: str) -> SimpleNamespace | str | None:
        """Return a Jira issue by key.

        :param issue_key: The key of the issue to retrieve.
        :type issue_key: str
        :return: Issue data with fields accessible through dot notation, raw
            response text for non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        return self.get(url)

    def issue_changelog(self, issue_key: str) -> SimpleNamespace | str | None:
        """Return an issue with changelog data expanded.

        :param issue_key: The key of the issue to retrieve the changelog for.
        :type issue_key: str
        :return: Issue data including ``changelog`` and ``summary`` fields, raw
            response text for non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        return self.get(url, params={"expand": "changelog", "fields": "summary"})

    def update_issue_label(
        self,
        issue_key: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict | None:
        """Add and/or remove labels on an issue.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param add_labels: Labels to add to the issue.
        :type add_labels: list[str], optional
        :param remove_labels: Labels to remove from the issue.
        :type remove_labels: list[str], optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Add and/or remove components on an issue by component name.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param add_components: Component names to add.
        :type add_components: list[str], optional
        :param remove_components: Component names to remove.
        :type remove_components: list[str], optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Replace an issue description.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param new_description: The new description for the issue.
        :type new_description: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Add and/or remove named values from an issue field.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param field_name: Jira field name or custom field ID to update.
        :type field_name: str
        :param add: Value name to add to the field.
        :type add: str, optional
        :param remove: Value name to remove from the field.
        :type remove: str, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Add a plain text comment to an issue.

        :param issue_key: The key of the issue to add a comment to.
        :type issue_key: str
        :param content: The content of the comment.
        :type content: str, optional

        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment"
        json = {"body": content}
        return self.post(url, json=json)

    def delete_issue_comment(self, issue_key: str, comment_id: str) -> dict | None:
        """Delete a comment from an issue by comment ID.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param comment_id: The ID of the comment to delete.
        :type comment_id: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Link two issues with a Jira issue-link relationship.

        :param type_name: The type of the link (e.g., "Dependence", "Blocking").
        :type type_name: str, optional
        :param inward_issue: The key of the inward issue.
        :type inward_issue: str, optional
        :param outward_issue: The key of the outward issue.
        :type outward_issue: str, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Delete an issue link by link ID."""
        url = f"/rest/api/2/issueLink/{link_id}"
        return self.delete(url)

    def create_issue(self, fields: dict, update: dict | None = None) -> dict | None:
        """Create an issue or sub-task from a Jira ``fields`` payload.

        :param fields: Jira fields payload. Common required keys are
            ``project``, ``summary``, and ``issuetype``.
        :type fields: dict
        :param update: Optional Jira update payload, for example to add
            worklog data while creating the issue.
        :type update: dict, optional

        :return: Decoded API response, or ``None`` when Jira returns no body.
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
        """Create a task with the legacy project-specific payload.

        .. deprecated::
            Use :meth:`create_issue` instead. ``create_task()`` contains
            hard-coded private custom fields (``customfield_11386``) that are
            not portable across Jira projects and will be removed in a future
            version.

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
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        warnings.warn(
            "create_task() is deprecated and will be removed in a future version. "
            "Use create_issue() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
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
        """Create a sub-task with the legacy project-specific payload.

        .. deprecated::
            Use :meth:`create_issue` instead. ``create_sub_task()`` contains
            hard-coded private custom fields (``customfield_13430``,
            ``customfield_11360``) that are not portable across Jira projects
            and will be removed in a future version.

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
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        warnings.warn(
            "create_sub_task() is deprecated and will be removed in a future version. "
            "Use create_issue() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
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
        """Update a Jira custom field.

        :param issue_key: The key of the issue to update.
        :type issue_key: str
        :param field_id: The ID of the custom field to update.
        :type field_id: str
        :param field_args: One value to set directly, or two values to set a
            nested object such as ``{"name": "value"}``.
        :type field_args: tuple
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        :raises AttributeError: If more than two ``field_args`` are provided.
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
        """Assign an issue to a user or unassign it.

        :param issue_key: The key of the issue to assign.
        :type issue_key: str
        :param assignee: Username to assign. When omitted, ``-1`` is sent to
            unassign the issue.
        :type assignee: str, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/assignee"
        # Pass -1 to unassign; JIRA API accepts either a username string or -1
        name: str | int = assignee if assignee is not None else -1
        json = {"name": name}
        return self.put(url, json=json)

    def add_issue_watcher(self, issue_key: str, watcher: str) -> dict | None:
        """Add a user as an issue watcher.

        :param issue_key: The key of the issue to add a watcher to.
        :type issue_key: str
        :param watcher: The username of the watcher.
        :type watcher: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/watchers"
        # JIRA API expects the username as a raw JSON string body
        return self.post(url, json=watcher)  # type: ignore[arg-type]

    def issue_transition(
        self, issue_key: str, transition_id: str | None = None
    ) -> dict | None:
        """Move an issue through a Jira workflow transition.

        Transition IDs vary by project and workflow. Call
        :meth:`get_transitions` first to list the transitions available to the
        current user, then pass the selected transition ID here.

        :param issue_key: The key of the issue to transition.
        :type issue_key: str
        :param transition_id: The ID of the transition to perform.
        :type transition_id: str, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = "/rest/api/2/issue/{key}/transitions".format(key=issue_key)
        json = {"transition": {"id": transition_id}}
        return self.post(url, json=json)

    def get_transitions(self, issue_id: str) -> SimpleNamespace | str | None:
        """Return transitions available for an issue to the current user.

        :param issue_id: The ID of the issue to get transitions for.
        :type issue_id: str
        :return: Transition data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_id}/transitions"
        return self.get(url)

    def search_issue_with_jql(
        self,
        jql: str,
        max_result: int = 1000,
        fields: list[str] | None = None,
    ) -> list:
        """Search issues using JQL.

        :param jql: The JQL query string.
        :type jql: str
        :param max_result: Page size requested from Jira for each API call.
        :type max_result: int, optional
        :param fields: List of field names to return for each issue. When
            ``None`` (the default), all fields are returned. Pass an explicit
            list to restrict the response, for example
            ``["summary", "status", "assignee"]``.
        :type fields: list[str], optional
        :return: Issues matching the query.
        :rtype: list
        """
        url = "/rest/api/2/search"
        start_at = 0
        issues: list[str] = []
        payload: dict = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_result,
        }
        if fields is not None:
            payload["fields"] = fields
        response = self.post(url, json=payload) or {}
        try:
            total = response["total"]
        except KeyError:
            return issues
        max_results = response["maxResults"]
        for issue in response["issues"]:
            issues.append(issue)

        while total > max_results:
            start_at = start_at + max_results
            payload = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_result,
            }
            if fields is not None:
                payload["fields"] = fields
            response = self.post(url, json=payload) or {}
            total = total - max_results
            for issue in response["issues"]:
                issues.append(issue)
        return issues

    def get_project_components(self, project_id: str) -> SimpleNamespace | str | None:
        """Return components configured for a Jira project.

        :param project_id: The ID of the project to get components for.
        :type project_id: str
        :return: Project components, raw response text for non-JSON responses,
            or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/project/{project_id}/components"
        return self.get(url)

    def user(self, username: str) -> SimpleNamespace | str | None:
        """Return Jira user information by username.

        :param username: The username of the user to retrieve.
        :type username: str
        :return: User data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/user?username={username}"
        return self.get(url)

    def get_dev_status(
        self,
        issue_id: str,
        app_type: str = "stash",
        data_type: str = "repository",
    ) -> SimpleNamespace | str | None:
        """Return linked development status for an issue.

        :param issue_id: The ID of the issue to get development status for.
        :type issue_id: str
        :param app_type: The type of application (default is "stash").
        :type app_type: str, optional
        :param data_type: The type of data (default is "repository").
        :type data_type: str, optional
        :return: Development status data, raw response text for non-JSON
            responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/dev-status/1.0/issue/detail?issueId={issue_id}&applicationType={app_type}&dataType={data_type}"
        return self.get(url)

    def delete_issue(self, issue_key: str) -> dict | None:
        """Delete an issue by key.

        :param issue_key: The key of the issue to delete.
        :type issue_key: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        return self.delete(url)

    def get_project(self, project_key: str) -> SimpleNamespace | str | None:
        """Return a Jira project by project key.

        :param project_key: The key of the project to retrieve.
        :type project_key: str
        :return: Project data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/project/{project_key}"
        return self.get(url)

    def get_projects(self) -> SimpleNamespace | str | None:
        """Return projects visible to the current user.

        :return: Project list, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/2/project"
        return self.get(url)

    def get_issue_comments(self, issue_key: str) -> SimpleNamespace | str | None:
        """Return comments for an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :return: Comment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment"
        return self.get(url)

    def update_issue_comment(
        self, issue_key: str, comment_id: str, content: str
    ) -> dict | None:
        """Replace the body of an existing issue comment.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param comment_id: The ID of the comment to update.
        :type comment_id: str
        :param content: The new content of the comment.
        :type content: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        json = {"body": content}
        return self.put(url, json=json)

    def get_issue_watchers(self, issue_key: str) -> SimpleNamespace | str | None:
        """Return watchers for an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :return: Watcher data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}/watchers"
        return self.get(url)

    def get_versions(self, project_key: str) -> SimpleNamespace | str | None:
        """Return versions configured for a Jira project.

        :param project_key: The key of the project.
        :type project_key: str
        :return: Version data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
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
        """Create a version in a Jira project.

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
        :return: Decoded API response, or ``None`` when Jira returns no body.
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

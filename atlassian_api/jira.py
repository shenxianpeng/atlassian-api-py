from __future__ import annotations

from types import SimpleNamespace

from atlassian_api.client import AtlassianAPI
from atlassian_api.logger import get_logger

logger = get_logger(__name__)


class Jira(AtlassianAPI):
    """Client for Jira REST API operations on Cloud and Server/Data Center.

    Use this class for issue lookup, issue updates, JQL searches, comments,
    watchers, transitions, projects, and versions. Responses from read methods
    are usually nested ``SimpleNamespace`` objects; methods that mutate Jira
    return decoded JSON dictionaries or ``None`` for empty responses.

    The same calls work on both deployments. On Jira Cloud (detected from a
    ``*.atlassian.net`` URL, or ``cloud=True``) the client uses the Cloud
    endpoints where they differ, and users are identified by ``accountId``
    instead of username.

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
        :param assignee: Username (Server/Data Center) or ``accountId``
            (Cloud) to assign. When omitted, the issue is unassigned. Pass
            ``"-1"`` to use the project's automatic assignee.
        :type assignee: str, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/2/issue/{issue_key}/assignee"
        # Jira: a null name unassigns the issue, "-1" picks the automatic assignee.
        json = {self._user_field: assignee}
        return self.put(url, json=json)

    @property
    def _user_field(self) -> str:
        """Payload key that identifies a user: ``accountId`` on Cloud."""
        return "accountId" if self.cloud else "name"

    def add_issue_watcher(self, issue_key: str, watcher: str) -> dict | None:
        """Add a user as an issue watcher.

        :param issue_key: The key of the issue to add a watcher to.
        :type issue_key: str
        :param watcher: Username (Server/Data Center) or ``accountId``
            (Cloud) of the watcher.
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
    ) -> list[dict]:
        """Search issues using JQL and return every matching issue.

        All result pages are fetched. On Server/Data Center this uses
        ``/rest/api/2/search``; on Cloud, where that endpoint was removed
        (HTTP 410), it uses ``/rest/api/2/search/jql`` and follows
        ``nextPageToken``. Cloud requires a *bounded* query, for example one
        that restricts ``project``.

        :param jql: The JQL query string.
        :type jql: str
        :param max_result: Page size requested from Jira for each API call.
        :type max_result: int, optional
        :param fields: List of field names to return for each issue. When
            ``None`` (the default), Jira's navigable fields are returned on
            both deployments. Pass an explicit list to restrict the response,
            for example ``["summary", "status", "assignee"]``.
        :type fields: list[str], optional
        :return: Issues matching the query.
        :rtype: list
        """
        if self.cloud:
            return self._search_issue_with_jql_cloud(jql, max_result, fields)
        url = "/rest/api/2/search"
        start_at = 0
        issues: list[dict] = []
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

    def _search_issue_with_jql_cloud(
        self, jql: str, max_result: int, fields: list[str] | None
    ) -> list[dict]:
        """Run a JQL search on Jira Cloud's enhanced search endpoint."""
        url = "/rest/api/2/search/jql"
        payload: dict = {
            "jql": jql,
            "maxResults": max_result,
            # The enhanced endpoint returns only issue IDs unless asked.
            "fields": fields if fields is not None else ["*navigable"],
        }
        issues: list[dict] = []
        while True:
            response = self.post(url, json=payload) or {}
            page = response.get("issues") or []
            issues.extend(page)
            token = response.get("nextPageToken")
            # Stop on the last page; also guard against a token that keeps
            # coming back with no issues.
            if response.get("isLast") or not token or not page:
                return issues
            payload["nextPageToken"] = token

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
        """Return Jira user information.

        :param username: Username (Server/Data Center) or ``accountId``
            (Cloud) of the user to retrieve.
        :type username: str
        :return: User data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/2/user"
        key = "accountId" if self.cloud else "username"
        return self.get(url, params={key: username})

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
        url = "/rest/dev-status/1.0/issue/detail"
        params = {
            "issueId": issue_id,
            "applicationType": app_type,
            "dataType": data_type,
        }
        return self.get(url, params=params)

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

    def get_projects(self) -> list | SimpleNamespace | str | None:
        """Return projects visible to the current user.

        On Cloud, where the unpaginated endpoint is deprecated, all pages of
        ``/rest/api/2/project/search`` are collected into one list so the
        result has the same shape as on Server/Data Center.

        :return: Project list, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: list or SimpleNamespace or str or None
        """
        if not self.cloud:
            return self.get("/rest/api/2/project")
        projects: list = []
        params: dict = {"startAt": 0, "maxResults": 50}
        while True:
            page = self.get("/rest/api/2/project/search", params=params)
            values = getattr(page, "values", None) or []
            projects.extend(values)
            if not values or getattr(page, "isLast", True):
                return projects
            params["startAt"] += len(values)

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
        payload: dict = {"name": name, "released": released}
        if self.cloud:
            # Cloud dropped the project key here; it needs the numeric ID.
            project = self.get_project(project_key)
            payload["projectId"] = int(getattr(project, "id"))
        else:
            payload["project"] = project_key
        if description is not None:
            payload["description"] = description
        if start_date is not None:
            payload["startDate"] = start_date
        if release_date is not None:
            payload["releaseDate"] = release_date
        return self.post(url, json=payload)

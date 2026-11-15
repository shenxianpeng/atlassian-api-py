from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

from atlassian_api.client import AtlassianAPI, _same_origin
from atlassian_api.error import APIError
from atlassian_api.logger import get_logger

logger = get_logger(__name__)

#: Jira Software (Agile) REST API: boards, sprints and epics.
_AGILE = "/rest/agile/1.0"
#: Where Jira Cloud serves the issues of a board, sprint or epic.
_SOFTWARE = "/rest/software/1.0"
#: Boards, sprints or epics requested per page (Jira's default page size).
_AGILE_PAGE_SIZE = 50
#: Most issues Jira accepts in one "move issues" request.
_MOVE_ISSUES_MAX = 50


class Jira(AtlassianAPI):
    """Client for Jira REST API operations on Cloud and Server/Data Center.

    Use this class for issue lookup, issue updates, JQL searches, comments,
    watchers, transitions, projects, versions, and Jira Software boards,
    sprints and epics. Responses from read methods are usually nested
    ``SimpleNamespace`` objects; methods that mutate Jira return decoded JSON
    dictionaries or ``None`` for empty responses.

    The same calls work on both deployments. On Jira Cloud (detected from a
    ``*.atlassian.net`` URL, or ``cloud=True``) the client uses the Cloud
    endpoints where they differ, and users are identified by ``accountId``
    instead of username.

    .. seealso::
        `Jira REST API Documentation <https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/>`_

        Jira Software REST API for
        `Cloud <https://developer.atlassian.com/cloud/jira/software/rest/>`_ and
        `Data Center <https://docs.atlassian.com/jira-software/REST/latest/>`_
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

        On Cloud, ``expand=changelog`` returns only recent updates, so the full
        history is read from the paginated ``/changelog`` endpoint and returned
        in the same ``changelog.histories`` shape.

        :param issue_key: The key of the issue to retrieve the changelog for.
        :type issue_key: str
        :return: Issue data including ``changelog`` and ``summary`` fields, raw
            response text for non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/2/issue/{issue_key}"
        if not self.cloud:
            return self.get(url, params={"expand": "changelog", "fields": "summary"})
        issue = self.get(url, params={"fields": "summary"})
        if not isinstance(issue, SimpleNamespace):
            return issue
        histories: list = []
        start = 0
        while True:
            page = self.get(
                f"{url}/changelog", params={"startAt": start, "maxResults": 100}
            )
            values = getattr(page, "values", None) or []
            histories.extend(values)
            start += len(values)
            if not values or getattr(page, "isLast", True):
                break
        issue.changelog = SimpleNamespace(
            startAt=0,
            maxResults=len(histories),
            total=len(histories),
            histories=histories,
        )
        return issue

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

        All result pages are fetched; see :meth:`iter_issues` to process
        issues as they arrive instead of holding them all in memory.

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
        return list(self.iter_issues(jql, fields=fields, page_size=max_result))

    def iter_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> Iterator[dict]:
        """Yield every issue matching a JQL query, one page at a time.

        On Server/Data Center this pages ``/rest/api/2/search`` with
        ``startAt``. On Cloud, where that endpoint was removed (HTTP 410), it
        uses ``/rest/api/2/search/jql`` and follows ``nextPageToken``; Cloud
        requires a *bounded* query, for example one that restricts
        ``project``.

        .. code-block:: python

            for issue in jira.iter_issues("project = TEST", fields=["summary"]):
                print(issue["key"], issue["fields"]["summary"])

        :param jql: The JQL query string.
        :type jql: str
        :param fields: Fields to return. ``None`` returns navigable fields.
        :type fields: list[str], optional
        :param page_size: Issues requested per API call.
        :type page_size: int, optional
        :return: Issue dictionaries.
        :rtype: Iterator[dict]
        """
        if self.cloud:
            yield from self._iter_issues_cloud(jql, fields, page_size)
            return
        start_at = 0
        while True:
            payload: dict = {"jql": jql, "startAt": start_at, "maxResults": page_size}
            if fields is not None:
                payload["fields"] = fields
            response = self.post("/rest/api/2/search", json=payload) or {}
            page = response.get("issues") or []
            yield from page
            start_at += len(page)
            if not page or start_at >= response.get("total", 0):
                return

    def _iter_issues_cloud(
        self, jql: str, fields: list[str] | None, page_size: int
    ) -> Iterator[dict]:
        """Page through Jira Cloud's enhanced search endpoint."""
        payload: dict = {
            "jql": jql,
            "maxResults": page_size,
            # The enhanced endpoint returns only issue IDs unless asked.
            "fields": fields if fields is not None else ["*navigable"],
        }
        while True:
            response = self.post("/rest/api/2/search/jql", json=payload) or {}
            page = response.get("issues") or []
            yield from page
            token = response.get("nextPageToken")
            # Stop on the last page; also guard against a token that keeps
            # coming back with no issues.
            if response.get("isLast") or not token or not page:
                return
            payload["nextPageToken"] = token

    def count_issues(self, jql: str) -> int:
        """Return how many issues match a JQL query.

        Cloud's search no longer reports a total, so this uses
        ``/rest/api/2/search/approximate-count`` there (the count can lag
        recent changes by a few seconds). Server/Data Center reads ``total``
        from a search that returns no issues.

        :param jql: The JQL query string.
        :type jql: str
        :return: Number of matching issues.
        :rtype: int
        """
        if self.cloud:
            response = self.post(
                "/rest/api/2/search/approximate-count", json={"jql": jql}
            )
            return int((response or {}).get("count", 0))
        payload = {"jql": jql, "maxResults": 0, "fields": ["id"]}
        response = self.post("/rest/api/2/search", json=payload)
        return int((response or {}).get("total", 0))

    def update_issue(
        self,
        issue_key: str,
        fields: dict | None = None,
        update: dict | None = None,
        notify_users: bool = True,
    ) -> dict | None:
        """Edit an issue with Jira's ``fields`` and/or ``update`` payloads.

        .. code-block:: python

            jira.update_issue(
                "TEST-1",
                fields={"summary": "New title", jira.get_field_id("Story Points"): 3},
                update={"labels": [{"add": "triaged"}]},
            )

        :param issue_key: The key of the issue to edit.
        :type issue_key: str
        :param fields: Field values to set, keyed by field ID.
        :type fields: dict, optional
        :param update: Jira update operations, for example ``add``/``remove``.
        :type update: dict, optional
        :param notify_users: Send notification emails. Turning this off needs
            admin or project-admin permission.
        :type notify_users: bool, optional
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        payload: dict = {}
        if fields:
            payload["fields"] = fields
        if update:
            payload["update"] = update
        params = None if notify_users else {"notifyUsers": "false"}
        return self.put(f"/rest/api/2/issue/{issue_key}", json=payload, params=params)

    def get_fields(self) -> list | SimpleNamespace | str | None:
        """Return all system and custom fields.

        :return: Field objects with ``id``, ``name``, ``custom`` and ``schema``.
        :rtype: list or SimpleNamespace or str or None
        """
        return self.get("/rest/api/2/field")

    def get_field_id(self, name: str) -> str:
        """Return the ID of a field from its display name.

        Useful for custom fields, whose IDs (``customfield_10016``) differ
        between sites. Matching ignores case.

        :param name: Field name as shown in Jira, for example ``"Story Points"``.
        :type name: str
        :return: The field ID.
        :rtype: str
        :raises ValueError: If no field, or more than one field, has this name.
        """
        fields = self.get_fields()
        wanted = name.casefold()
        matches = [
            f.id
            for f in (fields if isinstance(fields, list) else [])
            if str(getattr(f, "name", "")).casefold() == wanted
        ]
        if len(matches) != 1:
            found = "No field" if not matches else f"{len(matches)} fields"
            raise ValueError(f"{found} named {name!r}: {matches}")
        return matches[0]

    def search_users(
        self, query: str, max_results: int = 50
    ) -> list | SimpleNamespace | str | None:
        """Find users by name, username or email.

        On Cloud the result contains ``accountId`` values to pass to
        :meth:`assign_issue` or :meth:`add_issue_watcher`.

        :param query: Text to match.
        :type query: str
        :param max_results: Maximum number of users to return.
        :type max_results: int, optional
        :return: Matching users.
        :rtype: list or SimpleNamespace or str or None
        """
        key = "query" if self.cloud else "username"
        params = {key: query, "maxResults": max_results}
        return self.get("/rest/api/2/user/search", params=params)

    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        comment: str | None = None,
        started: str | None = None,
    ) -> dict | None:
        """Log work on an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param time_spent: Duration in Jira format, for example ``"1h 30m"``.
        :type time_spent: str
        :param comment: Optional worklog comment.
        :type comment: str, optional
        :param started: Start time, for example
            ``"2026-10-26T09:00:00.000+0000"``. Defaults to now.
        :type started: str, optional
        :return: The created worklog.
        :rtype: dict or None
        """
        payload: dict[str, Any] = {"timeSpent": time_spent}
        if comment is not None:
            payload["comment"] = comment
        if started is not None:
            payload["started"] = started
        return self.post(f"/rest/api/2/issue/{issue_key}/worklog", json=payload)

    def get_worklogs(self, issue_key: str) -> SimpleNamespace | str | None:
        """Return worklogs of an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :return: Worklog page with a ``worklogs`` list.
        :rtype: SimpleNamespace or str or None
        """
        return self.get(f"/rest/api/2/issue/{issue_key}/worklog")

    def add_attachment(
        self,
        issue_key: str,
        filename: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> list | dict | None:
        """Attach a file to an issue.

        :param issue_key: The key of the issue.
        :type issue_key: str
        :param filename: Attachment file name.
        :type filename: str
        :param file_data: File contents.
        :type file_data: bytes
        :param content_type: MIME type of the file.
        :type content_type: str, optional
        :return: The created attachment objects.
        :rtype: list or dict or None
        """
        response = self.request(
            "POST",
            f"/rest/api/2/issue/{issue_key}/attachments",
            files={"file": (filename, file_data, content_type)},
            # Jira rejects multipart uploads without this CSRF bypass header.
            headers={"X-Atlassian-Token": "no-check"},
        )
        return self._response_handler(response)

    def get_attachment(self, attachment_id: str) -> SimpleNamespace | str | None:
        """Return attachment metadata, including the ``content`` download URL.

        :param attachment_id: The attachment ID.
        :type attachment_id: str
        :return: Attachment metadata.
        :rtype: SimpleNamespace or str or None
        """
        return self.get(f"/rest/api/2/attachment/{attachment_id}")

    def download_attachment(
        self, attachment_id: str, path: str | Path | None = None
    ) -> bytes | Path:
        """Download an attachment's contents.

        :param attachment_id: The attachment ID.
        :type attachment_id: str
        :param path: Where to write the file. The download is streamed to disk
            in chunks, so large files are not held in memory.
        :type path: str or pathlib.Path, optional
        :return: The file contents, or ``path`` when one was given.
        :rtype: bytes or pathlib.Path
        """
        meta = self.get_attachment(attachment_id)
        content_url = getattr(meta, "content", None)
        if not content_url:
            raise APIError(None, f"Attachment {attachment_id} has no content URL")
        mime = str(getattr(meta, "mimeType", "") or "")
        return self._download(
            self._on_client_host(content_url),
            path,
            reject_html=bool(mime) and not mime.startswith("text/html"),
        )

    def _on_client_host(self, url: str) -> str:
        """Point an attachment URL from Jira at the URL this client uses.

        Jira builds ``content`` links from its configured base URL, which can
        differ from the URL a script reaches it on (an internal host name,
        another port, the Cloud API gateway). The path from
        ``/secure/attachment/`` or ``/rest/`` on is kept.
        """
        parts = urlsplit(url)
        if not parts.scheme or _same_origin(parts, urlsplit(self.url)):
            return url
        for marker in ("/secure/attachment/", "/rest/"):
            index = parts.path.find(marker)
            if index != -1:
                rest = parts.path[index:]
                return self.url + rest + (f"?{parts.query}" if parts.query else "")
        return url

    def delete_attachment(self, attachment_id: str) -> dict | None:
        """Delete an attachment.

        :param attachment_id: The attachment ID.
        :type attachment_id: str
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        return self.delete(f"/rest/api/2/attachment/{attachment_id}")

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

    # ------------------------------------------------------------------
    # Jira Software (Agile): boards, sprints and epics
    # ------------------------------------------------------------------

    def _agile_values(
        self, path: str, params: dict | None = None, limit: int | None = None
    ) -> list:
        """Collect ``values`` from a paginated Jira Software endpoint.

        :param path: Endpoint path below ``/rest/agile/1.0``.
        :type path: str
        :param params: Query parameters; ``None`` values are not sent.
        :type params: dict, optional
        :param limit: Most items to return. ``None`` returns every page.
        :type limit: int, optional
        :return: Items from each page, in order.
        :rtype: list
        """
        if limit is not None and limit <= 0:
            return []
        # ``requests`` leaves out parameters whose value is None.
        query = {**(params or {}), "startAt": 0}
        values: list = []
        while True:
            query["maxResults"] = (
                _AGILE_PAGE_SIZE
                if limit is None
                else min(_AGILE_PAGE_SIZE, limit - len(values))
            )
            page = self.get(f"{_AGILE}{path}", params=query)
            items = getattr(page, "values", None) or []
            values.extend(items)
            # Jira may return fewer items than requested: advance by what
            # arrived, not by the page size.
            query["startAt"] += len(items)
            if not items or (limit is not None and len(values) >= limit):
                break
            is_last = getattr(page, "isLast", None)
            if is_last is None:
                # Without "isLast", go by "total"; Jira may leave that out
                # too, and then only an empty page ends the listing.
                total = getattr(page, "total", None)
                is_last = total is not None and query["startAt"] >= total
            if is_last:
                break
        return values if limit is None else values[:limit]

    def _iter_agile_issues(
        self,
        path: str,
        jql: str | None,
        fields: list[str] | None,
        page_size: int,
    ) -> Iterator[SimpleNamespace]:
        """Yield the issues of a board, sprint or epic, one page at a time.

        Server/Data Center pages ``/rest/agile/1.0`` with ``startAt``. Cloud
        deprecated those issue lists; there ``/rest/software/1.0`` is used,
        which pages with ``nextPageToken`` and reports no ``total``.

        :param path: Endpoint path below the API root, the same on both.
        :type path: str
        :param jql: JQL that narrows (and can reorder) the issues.
        :type jql: str or None
        :param fields: Fields to return. ``None`` returns navigable and Jira
            Software fields.
        :type fields: list[str] or None
        :param page_size: Issues requested per API call.
        :type page_size: int
        :return: Issue objects.
        :rtype: Iterator[SimpleNamespace]
        """
        params: dict = {"maxResults": page_size}
        if jql:
            params["jql"] = jql
        if fields is not None:
            params["fields"] = ",".join(fields)
        url = f"{_SOFTWARE if self.cloud else _AGILE}{path}"
        if not self.cloud:
            params["startAt"] = 0
        while True:
            page = self.get(url, params=params)
            issues = getattr(page, "issues", None) or []
            yield from issues
            if not issues:
                return
            if self.cloud:
                # The last page carries no token.
                token = getattr(page, "nextPageToken", None)
                if getattr(page, "isLast", False) or not token:
                    return
                params["nextPageToken"] = token
            else:
                # Jira may return fewer issues than requested: advance by
                # what arrived, not by the page size. "total" is optional;
                # without it only an empty page ends the listing.
                params["startAt"] += len(issues)
                total = getattr(page, "total", None)
                if total is not None and params["startAt"] >= total:
                    return

    def _move_issues(self, path: str, issues: str | Iterable[str | int]) -> None:
        """Post issue keys to a "move issues" endpoint, 50 per request.

        :param path: Endpoint path below ``/rest/agile/1.0``.
        :type path: str
        :param issues: Issue keys or IDs; one key may be given as a string.
            Duplicates are sent once.
        :type issues: str or Iterable[str or int]
        """
        if isinstance(issues, str):
            issues = [issues]
        keys = list(dict.fromkeys(str(issue) for issue in issues))
        for start in range(0, len(keys), _MOVE_ISSUES_MAX):
            chunk = keys[start : start + _MOVE_ISSUES_MAX]
            self.post(f"{_AGILE}{path}", json={"issues": chunk})

    def get_boards(
        self,
        project: str | None = None,
        name: str | None = None,
        board_type: str | None = None,
        limit: int | None = None,
    ) -> list:
        """Return the boards visible to the current user.

        All pages are collected unless ``limit`` is given.

        .. code-block:: python

            for board in jira.get_boards(project="TEST", board_type="scrum"):
                print(board.id, board.name)

        :param project: Key or ID of a project; only boards whose filter
            refers to that project are returned.
        :type project: str, optional
        :param name: Only boards whose name contains this text.
        :type name: str, optional
        :param board_type: ``"scrum"`` or ``"kanban"`` (Cloud also has
            ``"simple"``, the boards of team-managed projects).
        :type board_type: str, optional
        :param limit: Most boards to return. ``None`` returns all of them.
        :type limit: int, optional
        :return: Board objects with ``id``, ``name`` and ``type``.
        :rtype: list
        """
        params = {"projectKeyOrId": project, "name": name, "type": board_type}
        return self._agile_values("/board", params, limit)

    def get_board(self, board_id: int | str) -> SimpleNamespace | str | None:
        """Return a board by ID.

        :param board_id: The ID of the board.
        :type board_id: int or str
        :return: Board data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        return self.get(f"{_AGILE}/board/{board_id}")

    def get_board_sprints(
        self,
        board_id: int | str,
        state: str | None = None,
        limit: int | None = None,
    ) -> list:
        """Return the sprints of a board.

        Closed sprints come first, then active, then future ones. All pages
        are collected unless ``limit`` is given. Jira answers HTTP 400 for a
        board without sprints, such as a kanban board.

        .. code-block:: python

            active = jira.get_board_sprints(84, state="active")

        :param board_id: The ID of the board.
        :type board_id: int or str
        :param state: ``"future"``, ``"active"`` or ``"closed"``; separate
            several with commas, for example ``"active,future"``.
        :type state: str, optional
        :param limit: Most sprints to return. ``None`` returns all of them.
        :type limit: int, optional
        :return: Sprint objects with ``id``, ``name``, ``state`` and, once
            set, ``startDate``, ``endDate``, ``completeDate`` and ``goal``.
        :rtype: list
        """
        return self._agile_values(f"/board/{board_id}/sprint", {"state": state}, limit)

    def get_board_epics(
        self,
        board_id: int | str,
        done: bool | None = None,
        limit: int | None = None,
    ) -> list:
        """Return the epics on a board.

        All pages are collected unless ``limit`` is given.

        :param board_id: The ID of the board.
        :type board_id: int or str
        :param done: ``True`` for epics marked as done only, ``False`` for
            the others. ``None`` returns both.
        :type done: bool, optional
        :param limit: Most epics to return. ``None`` returns all of them.
        :type limit: int, optional
        :return: Epic objects with ``id``, ``name``, ``summary`` and
            ``done``.
        :rtype: list
        """
        params = {"done": None if done is None else str(bool(done)).lower()}
        return self._agile_values(f"/board/{board_id}/epic", params, limit)

    def iter_board_issues(
        self,
        board_id: int | str,
        jql: str | None = None,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> Iterator[SimpleNamespace]:
        """Yield every issue on a board, ordered by rank.

        An issue is on the board when its status is mapped to one of the
        board's columns. Epics are not part of a scrum board.

        Unlike :meth:`iter_issues`, issues are ``SimpleNamespace`` objects, as
        returned by :meth:`issue`, with the Jira Software fields ``sprint``,
        ``closedSprints``, ``flagged`` and ``epic`` added.

        On Cloud, where ``/rest/agile/1.0/board/{id}/issue`` is deprecated,
        ``/rest/software/1.0/board/{id}/issue`` is used and paged with
        ``nextPageToken``.

        :param board_id: The ID of the board.
        :type board_id: int or str
        :param jql: JQL that narrows the issues, for example
            ``"status != Done"``. An ``ORDER BY`` replaces the rank order.
        :type jql: str, optional
        :param fields: Fields to return. ``None`` returns navigable and Jira
            Software fields.
        :type fields: list[str], optional
        :param page_size: Issues requested per API call.
        :type page_size: int, optional
        :return: Issue objects.
        :rtype: Iterator[SimpleNamespace]
        """
        return self._iter_agile_issues(
            f"/board/{board_id}/issue", jql, fields, page_size
        )

    def iter_backlog_issues(
        self,
        board_id: int | str,
        jql: str | None = None,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> Iterator[SimpleNamespace]:
        """Yield every issue in a board's backlog, ordered by rank.

        The backlog holds the unfinished issues that are in no active or
        future sprint. Paging and issue objects are those of
        :meth:`iter_board_issues`.

        :param board_id: The ID of the board.
        :type board_id: int or str
        :param jql: JQL that narrows the issues.
        :type jql: str, optional
        :param fields: Fields to return. ``None`` returns navigable and Jira
            Software fields.
        :type fields: list[str], optional
        :param page_size: Issues requested per API call.
        :type page_size: int, optional
        :return: Issue objects.
        :rtype: Iterator[SimpleNamespace]
        """
        return self._iter_agile_issues(
            f"/board/{board_id}/backlog", jql, fields, page_size
        )

    def get_sprint(self, sprint_id: int | str) -> SimpleNamespace | str | None:
        """Return a sprint by ID.

        :param sprint_id: The ID of the sprint.
        :type sprint_id: int or str
        :return: Sprint data with ``id``, ``name``, ``state``,
            ``originBoardId`` and, once set, the dates and ``goal``; raw
            response text for non-JSON responses, or ``None`` for an empty
            body.
        :rtype: SimpleNamespace or str or None
        """
        return self.get(f"{_AGILE}/sprint/{sprint_id}")

    def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> dict | None:
        """Create a future sprint on a board.

        .. code-block:: python

            sprint = jira.create_sprint(
                84,
                "Sprint 12",
                start_date="2026-11-16T09:00:00.000+0000",
                end_date="2026-11-27T17:00:00.000+0000",
                goal="Ship the importer",
            )
            jira.move_issues_to_sprint(sprint["id"], ["TEST-1", "TEST-2"])

        :param board_id: The ID of the board the sprint belongs to.
        :type board_id: int
        :param name: The name of the sprint. Jira trims it.
        :type name: str
        :param start_date: Planned start, as an ISO 8601 date-time.
        :type start_date: str, optional
        :param end_date: Planned end, as an ISO 8601 date-time.
        :type end_date: str, optional
        :param goal: The sprint goal.
        :type goal: str, optional
        :return: The created sprint.
        :rtype: dict or None
        """
        payload: dict[str, Any] = {"name": name, "originBoardId": board_id}
        if start_date is not None:
            payload["startDate"] = start_date
        if end_date is not None:
            payload["endDate"] = end_date
        if goal is not None:
            payload["goal"] = goal
        return self.post(f"{_AGILE}/sprint", json=payload)

    def update_sprint(
        self,
        sprint_id: int | str,
        name: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> dict | None:
        """Change some fields of a sprint; the others keep their value.

        This is Jira's partial update. Start a sprint with
        ``state="active"`` (it must be a future sprint with a start and an
        end date) and complete it with ``state="closed"`` (it must be
        active); no other state change is allowed.

        .. code-block:: python

            jira.update_sprint(37, state="active")
            jira.update_sprint(37, goal="Ship the importer")

        A closed sprint cannot be updated on Server/Data Center; on Cloud
        only its name and goal can.

        :param sprint_id: The ID of the sprint.
        :type sprint_id: int or str
        :param name: New name.
        :type name: str, optional
        :param state: ``"active"`` to start the sprint, ``"closed"`` to
            complete it.
        :type state: str, optional
        :param start_date: New start, as an ISO 8601 date-time.
        :type start_date: str, optional
        :param end_date: New end, as an ISO 8601 date-time.
        :type end_date: str, optional
        :param goal: New goal. An empty string removes it.
        :type goal: str, optional
        :return: The updated sprint.
        :rtype: dict or None
        """
        values = {
            "name": name,
            "state": state,
            "startDate": start_date,
            "endDate": end_date,
            "goal": goal,
        }
        payload = {key: value for key, value in values.items() if value is not None}
        # POST is the partial update; PUT would reset every field left out.
        return self.post(f"{_AGILE}/sprint/{sprint_id}", json=payload)

    def delete_sprint(self, sprint_id: int | str) -> dict | None:
        """Delete a sprint; its open issues go back to the backlog.

        Server/Data Center refuses to delete a sprint that is active or
        completed.

        :param sprint_id: The ID of the sprint.
        :type sprint_id: int or str
        :return: Decoded API response, or ``None`` when Jira returns no body.
        :rtype: dict or None
        """
        return self.delete(f"{_AGILE}/sprint/{sprint_id}")

    def iter_sprint_issues(
        self,
        sprint_id: int | str,
        jql: str | None = None,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> Iterator[SimpleNamespace]:
        """Yield every issue in a sprint, ordered by rank.

        .. code-block:: python

            for issue in jira.iter_sprint_issues(37, fields=["summary", "status"]):
                print(issue.key, issue.fields.status.name, issue.fields.summary)

        Paging and issue objects are those of :meth:`iter_board_issues`: on
        Cloud ``/rest/software/1.0/sprint/{id}/issue`` is used.

        :param sprint_id: The ID of the sprint.
        :type sprint_id: int or str
        :param jql: JQL that narrows the issues, for example
            ``"status != Done"``.
        :type jql: str, optional
        :param fields: Fields to return. ``None`` returns navigable and Jira
            Software fields.
        :type fields: list[str], optional
        :param page_size: Issues requested per API call.
        :type page_size: int, optional
        :return: Issue objects.
        :rtype: Iterator[SimpleNamespace]
        """
        return self._iter_agile_issues(
            f"/sprint/{sprint_id}/issue", jql, fields, page_size
        )

    def move_issues_to_sprint(
        self, sprint_id: int | str, issues: str | Iterable[str | int]
    ) -> None:
        """Move issues into an active or future sprint.

        Jira accepts 50 issues per request, so longer lists are sent in
        several requests. If one of them fails, the issues of the earlier
        requests have already been moved.

        :param sprint_id: The ID of the sprint.
        :type sprint_id: int or str
        :param issues: Issue keys or IDs.
        :type issues: str or Iterable[str or int]
        """
        self._move_issues(f"/sprint/{sprint_id}/issue", issues)

    def move_issues_to_backlog(self, issues: str | Iterable[str | int]) -> None:
        """Move issues out of their active or future sprint, into the backlog.

        Sent 50 issues per request, as :meth:`move_issues_to_sprint`.

        :param issues: Issue keys or IDs.
        :type issues: str or Iterable[str or int]
        """
        self._move_issues("/backlog/issue", issues)

    def get_epic(self, epic_id_or_key: int | str) -> SimpleNamespace | str | None:
        """Return an epic by issue ID or key.

        On Cloud this does not work for epics in team-managed projects; read
        those with :meth:`issue`.

        :param epic_id_or_key: The ID or key of the epic.
        :type epic_id_or_key: int or str
        :return: Epic data with ``id``, ``name``, ``summary`` and ``done``;
            raw response text for non-JSON responses, or ``None`` for an
            empty body.
        :rtype: SimpleNamespace or str or None
        """
        return self.get(f"{_AGILE}/epic/{epic_id_or_key}")

    def iter_epic_issues(
        self,
        epic_id_or_key: int | str,
        jql: str | None = None,
        fields: list[str] | None = None,
        page_size: int = 100,
    ) -> Iterator[SimpleNamespace]:
        """Yield every issue that belongs to an epic, ordered by rank.

        Paging and issue objects are those of :meth:`iter_board_issues`: on
        Cloud ``/rest/software/1.0/epic/{key}/issue`` is used.

        On Cloud this does not cover team-managed projects; search for the
        children instead: ``jira.iter_issues("parent = TEST-1")``.

        :param epic_id_or_key: The ID or key of the epic.
        :type epic_id_or_key: int or str
        :param jql: JQL that narrows the issues.
        :type jql: str, optional
        :param fields: Fields to return. ``None`` returns navigable and Jira
            Software fields.
        :type fields: list[str], optional
        :param page_size: Issues requested per API call.
        :type page_size: int, optional
        :return: Issue objects.
        :rtype: Iterator[SimpleNamespace]
        """
        return self._iter_agile_issues(
            f"/epic/{epic_id_or_key}/issue", jql, fields, page_size
        )

    def move_issues_to_epic(
        self, epic_id_or_key: int | str, issues: str | Iterable[str | int]
    ) -> None:
        """Put issues into an epic; an issue leaves the epic it was in.

        Sent 50 issues per request, as :meth:`move_issues_to_sprint`.

        On Cloud this does not work for epics in team-managed projects; set
        the parent there:
        ``jira.update_issue("TEST-2", fields={"parent": {"key": "TEST-1"}})``.

        :param epic_id_or_key: The ID or key of the epic.
        :type epic_id_or_key: int or str
        :param issues: Issue keys or IDs.
        :type issues: str or Iterable[str or int]
        """
        self._move_issues(f"/epic/{epic_id_or_key}/issue", issues)

    def remove_issues_from_epic(self, issues: str | Iterable[str | int]) -> None:
        """Take issues out of the epic they belong to.

        Sent 50 issues per request, as :meth:`move_issues_to_sprint`. On
        Cloud this does not work for issues in team-managed projects.

        :param issues: Issue keys or IDs.
        :type issues: str or Iterable[str or int]
        """
        self._move_issues("/epic/none/issue", issues)

from __future__ import annotations

from typing import Any
from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Confluence(AtlassianAPI):
    """Client for Confluence REST API operations.

    Use this class for pages, spaces, content search, child pages, attachments,
    and labels. Read methods return nested ``SimpleNamespace`` objects when the
    API returns JSON, raw text for non-JSON responses, or ``None`` for empty
    responses.

    .. seealso::
        `Confluence REST API Documentation <https://docs.atlassian.com/ConfluenceServer/rest/7.17.2/>`_
    """

    def get_content(self) -> SimpleNamespace | str | None:
        """Return content visible to the current user.

        :return: Content data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content"
        return self.get(url)

    def create_content(
        self,
        title: str,
        space_key: str,
        body_value: str,
        ancestors_id: int | None = None,
        type: str = "page",
    ) -> dict | None:
        """Create a Confluence page or another content type.

        :param title: The title of the content.
        :type title: str
        :param space_key: The key of the space where the content will be created.
        :type space_key: str
        :param body_value: Body content in Confluence storage format.
        :type body_value: str
        :param ancestors_id: Parent content ID. When provided, the new page is
            created as a child of that content.
        :type ancestors_id: int, optional
        :param type: Content type, for example ``page``.
        :type type: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = "/rest/api/content"
        payload: dict[str, Any] = {
            "type": f"{type}",
            "title": f"{title}",
            "space": {"key": f"{space_key}"},
            "body": {
                "storage": {"value": f"{body_value}", "representation": "storage"}
            },
        }
        if ancestors_id is not None:
            payload["ancestors"] = [{"id": ancestors_id}]
        return self.post(url, json=payload)

    def update_content(
        self,
        page_id: int,
        title: str,
        body_value: str,
        type: str = "page",
        version: int | None = None,
    ) -> dict | None:
        """Update an existing Confluence content item.

        The Confluence API requires that the version number supplied is exactly
        the current version incremented by one. When ``version`` is not
        provided this method fetches the current version automatically.

        :param page_id: The ID of the content to update.
        :type page_id: int
        :param title: The new title of the content.
        :type title: str
        :param body_value: New body content in Confluence storage format.
        :type body_value: str
        :param type: Content type, for example ``page``.
        :type type: str
        :param version: Version number to submit. When omitted, the current
            version is retrieved from the API and incremented by one.
        :type version: int, optional
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        if version is None:
            current = self.get(
                f"/rest/api/content/{page_id}", params={"expand": "version"}
            )
            if isinstance(current, SimpleNamespace):
                version = current.version.number + 1
            else:
                version = 1
        url = f"/rest/api/content/{page_id}"
        json = {
            "version": {"number": version},
            "title": f"{title}",
            "type": f"{type}",
            "body": {
                "storage": {"value": f"{body_value}", "representation": "storage"}
            },
        }
        return self.put(url, json=json)

    def delete_content(self, page_id: int) -> dict | None:
        """Delete content from Confluence by content ID.

        :param page_id: The ID of the content to delete.
        :type page_id: int
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}"
        return self.delete(url)

    def get_content_by_id(self, page_id: int) -> SimpleNamespace | str | None:
        """Return content by content ID.

        :param page_id: The ID of the content to retrieve.
        :type page_id: int
        :return: Content data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}"
        return self.get(url)

    def get_content_history(self, page_id: int) -> SimpleNamespace | str | None:
        """Return version history for a content item.

        :param page_id: The ID of the content to retrieve the history for.
        :type page_id: int
        :return: History data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/history"
        return self.get(url)

    def get_spaces(
        self, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """Return Confluence spaces visible to the current user.

        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of spaces to return (default 25).
        :type limit: int, optional
        :return: Space data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/space"
        params: dict[str, Any] = {"start": start, "limit": limit}
        return self.get(url, params=params)

    def get_space(self, space_key: str) -> SimpleNamespace | str | None:
        """Return a Confluence space by space key.

        :param space_key: The key of the space to retrieve.
        :type space_key: str
        :return: Space data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/space/{space_key}"
        return self.get(url)

    def get_content_by_space(
        self,
        space_key: str,
        content_type: str = "page",
        start: int = 0,
        limit: int = 25,
    ) -> SimpleNamespace | str | None:
        """Return pages or blog posts in a Confluence space.

        :param space_key: The key of the space.
        :type space_key: str
        :param content_type: The type of content to retrieve ("page" or "blogpost"). Defaults to "page".
        :type content_type: str, optional
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: Content list data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content"
        params: dict[str, Any] = {
            "spaceKey": space_key,
            "type": content_type,
            "start": start,
            "limit": limit,
        }
        return self.get(url, params=params)

    def search_content(
        self, cql: str, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """Search content with Confluence Query Language (CQL).

        :param cql: The CQL query string.
        :type cql: str
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: Search result data, raw response text for non-JSON responses,
            or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content/search"
        params: dict[str, Any] = {"cql": cql, "start": start, "limit": limit}
        return self.get(url, params=params)

    def get_child_pages(
        self, page_id: int, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """Return child pages for a parent page.

        :param page_id: The ID of the parent page.
        :type page_id: int
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: Child page data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/page"
        params: dict[str, Any] = {"start": start, "limit": limit}
        return self.get(url, params=params)

    def get_attachments(self, page_id: int) -> SimpleNamespace | str | None:
        """Return attachments for a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: Attachment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/attachment"
        return self.get(url)

    def get_labels(self, page_id: int) -> SimpleNamespace | str | None:
        """Return labels for a content item.

        :param page_id: The ID of the content.
        :type page_id: int
        :return: Label data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/label"
        return self.get(url)

    def add_label(self, page_id: int, label: str) -> dict | None:
        """Add a global label to a content item.

        :param page_id: The ID of the content.
        :type page_id: int
        :param label: The label name to add.
        :type label: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        payload = [{"prefix": "global", "name": label}]
        return self.post(url, json=payload)

    def remove_label(self, page_id: int, label: str) -> dict | None:
        """Remove a label from a content item.

        :param page_id: The ID of the content.
        :type page_id: int
        :param label: The label name to remove.
        :type label: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        params: dict[str, Any] = {"name": label}
        return self.delete(url, params=params)

    def get_page_by_title(
        self, space_key: str, title: str
    ) -> SimpleNamespace | str | None:
        """Return a page by its title within a space.

        :param space_key: The key of the space to search in.
        :type space_key: str
        :param title: The exact title of the page.
        :type title: str
        :return: Content data for the matching page, raw response text for
            non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content"
        params: dict[str, Any] = {
            "spaceKey": space_key,
            "title": title,
            "type": "page",
        }
        return self.get(url, params=params)

    def upload_attachment(
        self,
        page_id: int,
        filename: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict | None:
        """Upload a file as an attachment to a page.

        :param page_id: The ID of the page to attach the file to.
        :type page_id: int
        :param filename: The name of the attachment file.
        :type filename: str
        :param file_data: The binary content of the file to upload.
        :type file_data: bytes
        :param content_type: The MIME type of the file (default
            ``application/octet-stream``).
        :type content_type: str, optional
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        from atlassian.error import APIError

        url = f"/rest/api/content/{page_id}/child/attachment"
        full_url = self.url + url
        self._session.headers["X-Atlassian-Token"] = "nocheck"
        try:
            response = self._session.post(
                full_url,
                files={"file": (filename, file_data, content_type)},
                data={"comment": ""},
                timeout=self.timeout,
            )
            response.encoding = "utf-8"
            if response.status_code >= 400:
                raise APIError(response.status_code, response.text)
            return self._response_handler(response)
        finally:
            self._session.headers.pop("X-Atlassian-Token", None)

    def get_comments(self, page_id: int) -> SimpleNamespace | str | None:
        """Return comments for a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: Comment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/comment"
        return self.get(url)

    def add_comment(self, page_id: int, body: str) -> dict | None:
        """Add a comment to a page.

        :param page_id: The ID of the page to comment on.
        :type page_id: int
        :param body: Comment body in Confluence storage format.
        :type body: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = "/rest/api/content"
        payload: dict[str, Any] = {
            "type": "comment",
            "container": {"id": page_id, "type": "page"},
            "body": {
                "storage": {"value": body, "representation": "storage"}
            },
        }
        return self.post(url, json=payload)

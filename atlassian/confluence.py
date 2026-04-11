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
    ) -> dict | None:
        """Update an existing Confluence content item.

        :param page_id: The ID of the content to update.
        :type page_id: int
        :param title: The new title of the content.
        :type title: str
        :param body_value: New body content in Confluence storage format.
        :type body_value: str
        :param type: Content type, for example ``page``.
        :type type: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}"
        json = {
            "version": {"number": 2},
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

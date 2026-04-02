from __future__ import annotations

from typing import Any
from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)


class Confluence(AtlassianAPI):
    """
    Confluence API Reference

    .. seealso::
        `Confluence REST API Documentation <https://docs.atlassian.com/ConfluenceServer/rest/7.17.2/>`_
    """

    def get_content(self) -> SimpleNamespace | str | None:
        """
        Retrieve all content from Confluence.

        :return: A SimpleNamespace containing all content, the raw text response, or None.
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
        """
        Create new content in Confluence.

        :param title: The title of the content.
        :type title: str
        :param space_key: The key of the space where the content will be created.
        :type space_key: str
        :param body_value: The body of the content in storage format.
        :type body_value: str
        :param ancestors_id: The ID of the parent content (optional).
        :type ancestors_id: int, optional
        :param type: The type of the content (e.g., "page").
        :type type: str
        :return: The response from the API.
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
        """
        Update existing content in Confluence.

        :param page_id: The ID of the content to update.
        :type page_id: int
        :param title: The new title of the content.
        :type title: str
        :param body_value: The new body of the content in storage format.
        :type body_value: str
        :param type: The type of the content (e.g., "page").
        :type type: str
        :return: The response from the API.
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
        """
        Delete content from Confluence.

        :param page_id: The ID of the content to delete.
        :type page_id: int
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}"
        return self.delete(url)

    def get_content_by_id(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Retrieve content by its ID.

        :param page_id: The ID of the content to retrieve.
        :type page_id: int
        :return: A SimpleNamespace containing the content details, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}"
        return self.get(url)

    def get_content_history(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Retrieve the history of a specific content.

        :param page_id: The ID of the content to retrieve the history for.
        :type page_id: int
        :return: A SimpleNamespace containing the content history.
        :rtype: SimpleNamespace or None
        """
        url = f"/rest/api/content/{page_id}/history"
        return self.get(url)

    def get_spaces(
        self, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """
        Retrieve all spaces.

        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of spaces to return (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing spaces, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/space"
        params: dict[str, Any] = {"start": start, "limit": limit}
        return self.get(url, params=params)

    def get_space(self, space_key: str) -> SimpleNamespace | str | None:
        """
        Retrieve a specific space by its key.

        :param space_key: The key of the space to retrieve.
        :type space_key: str
        :return: A SimpleNamespace containing the space details, the raw text response, or None.
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
        """
        Retrieve content (pages or blog posts) within a specific space.

        :param space_key: The key of the space.
        :type space_key: str
        :param content_type: The type of content to retrieve ("page" or "blogpost"). Defaults to "page".
        :type content_type: str, optional
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the content list, the raw text response, or None.
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
        """
        Search for content using Confluence Query Language (CQL).

        :param cql: The CQL query string.
        :type cql: str
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the search results, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content/search"
        params: dict[str, Any] = {"cql": cql, "start": start, "limit": limit}
        return self.get(url, params=params)

    def get_child_pages(
        self, page_id: int, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """
        Retrieve the child pages of a specific page.

        :param page_id: The ID of the parent page.
        :type page_id: int
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the child pages, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/page"
        params: dict[str, Any] = {"start": start, "limit": limit}
        return self.get(url, params=params)

    def get_attachments(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Retrieve all attachments for a specific page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the attachments, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/attachment"
        return self.get(url)

    def get_labels(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Retrieve all labels for a specific piece of content.

        :param page_id: The ID of the content.
        :type page_id: int
        :return: A SimpleNamespace containing the labels, the raw text response, or None.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/label"
        return self.get(url)

    def add_label(self, page_id: int, label: str) -> dict | None:
        """
        Add a label to a specific piece of content.

        :param page_id: The ID of the content.
        :type page_id: int
        :param label: The label name to add.
        :type label: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        payload = [{"prefix": "global", "name": label}]
        return self.post(url, json=payload)

    def remove_label(self, page_id: int, label: str) -> dict | None:
        """
        Remove a label from a specific piece of content.

        :param page_id: The ID of the content.
        :type page_id: int
        :param label: The label name to remove.
        :type label: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        params: dict[str, Any] = {"name": label}
        return self.delete(url, params=params)

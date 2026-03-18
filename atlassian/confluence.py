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

        :return: A SimpleNamespace containing all content.
        :rtype: SimpleNamespace or None
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
        if ancestors_id:
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
        :return: A SimpleNamespace containing the content details.
        :rtype: SimpleNamespace or None
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

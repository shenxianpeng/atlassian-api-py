from __future__ import annotations

from typing import Any
from types import SimpleNamespace

from atlassian.client import AtlassianAPI
from atlassian.error import APIError
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

        Fetches the current version number before writing so the PUT is always
        sent with the correct version.  Concurrent writes may still produce a
        409 Conflict — that is propagated as :class:`~atlassian.error.APIError`
        and is the caller's responsibility to handle.

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
        :raises APIError: If the current version cannot be fetched, or if the
            server returns an error (including 409 Conflict on concurrent write).
        """
        version = self.get_content_version(page_id)
        if version is None:
            raise APIError(-1, f"Unable to retrieve current version for page {page_id}")
        url = f"/rest/api/content/{page_id}"
        json = {
            "version": {"number": version + 1},
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

    def get_content_version(self, page_id: int) -> int | None:
        """
        Retrieve the current version number of a page.

        Uses the content history endpoint.  Returns ``None`` if the version
        cannot be determined (e.g. the page does not exist or the response is
        malformed).

        :param page_id: The ID of the content.
        :type page_id: int
        :return: The current version number, or None.
        :rtype: int or None
        """
        response = self.get_content_history(page_id)
        if response is None or isinstance(response, str):
            return None
        try:
            return response.lastUpdated.number
        except AttributeError:
            return None

    # ------------------------------------------------------------------ #
    # Search & spaces                                                      #
    # ------------------------------------------------------------------ #

    def search_content(
        self,
        cql: str,
        limit: int = 25,
    ) -> SimpleNamespace | str | None:
        """
        Search Confluence content using CQL.

        :param cql: A CQL query string (e.g. ``'type=page AND space="MYSPACE"'``).
        :type cql: str
        :param limit: Maximum number of results (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the search results.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content/search"
        return self.get(url, params={"cql": cql, "limit": limit})

    def get_space(self, space_key: str) -> SimpleNamespace | str | None:
        """
        Get a space by key.

        :param space_key: The space key.
        :type space_key: str
        :return: A SimpleNamespace containing the space details.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/space/{space_key}"
        return self.get(url)

    def list_spaces(self, limit: int = 25) -> SimpleNamespace | str | None:
        """
        List all spaces visible to the current user.

        :param limit: Maximum number of spaces to return (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the list of spaces.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/space"
        return self.get(url, params={"limit": limit})

    # ------------------------------------------------------------------ #
    # Page hierarchy                                                       #
    # ------------------------------------------------------------------ #

    def get_page_children(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get child pages of a page.

        :param page_id: The ID of the parent page.
        :type page_id: int
        :return: A SimpleNamespace containing the child pages.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/page"
        return self.get(url)

    def get_page_ancestors(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get ancestor pages of a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the ancestor pages.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/ancestor"
        return self.get(url)

    def move_page(
        self,
        page_id: int,
        target_id: int,
        position: str = "append",
    ) -> dict | None:
        """
        Move a page relative to another page.

        :param page_id: The ID of the page to move.
        :type page_id: int
        :param target_id: The ID of the target page.
        :type target_id: int
        :param position: Position relative to the target: ``"before"``,
            ``"after"``, or ``"append"`` (default).
        :type position: str, optional
        :return: The response from the API.
        :rtype: dict or None
        :raises ValueError: If *position* is not a valid value.
        """
        valid_positions = ("before", "after", "append")
        if position not in valid_positions:
            raise ValueError(
                f"position must be one of {valid_positions}, got {position!r}"
            )
        url = f"/rest/api/content/{page_id}/move/{position}/{target_id}"
        return self.put(url)

    # ------------------------------------------------------------------ #
    # Attachments                                                          #
    # ------------------------------------------------------------------ #

    def add_attachment(
        self,
        page_id: int,
        file_path: str,
        mime_type: str = "application/octet-stream",
    ) -> dict | None:
        """
        Attach a file to a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :param file_path: Path to the local file to attach.
        :type file_path: str
        :param mime_type: MIME type of the file (default ``application/octet-stream``).
        :type mime_type: str, optional
        :return: The attachment metadata returned by the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/child/attachment"
        return self.upload(url, file_path, mime_type)

    def get_attachments(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get attachments for a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the attachment metadata.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/attachment"
        return self.get(url)

    def delete_attachment(self, attachment_id: str) -> dict | None:
        """
        Delete an attachment by ID.

        :param attachment_id: The ID of the attachment content object.
        :type attachment_id: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{attachment_id}"
        return self.delete(url)

    # ------------------------------------------------------------------ #
    # Labels                                                               #
    # ------------------------------------------------------------------ #

    def get_labels(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get labels for a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the labels.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/label"
        return self.get(url)

    def add_label(self, page_id: int, label: str) -> dict | None:
        """
        Add a label to a page.

        :param page_id: The ID of the page.
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
        Remove a label from a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :param label: The label name to remove.
        :type label: str
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        return self.delete(url, params={"name": label})

    # ------------------------------------------------------------------ #
    # Comments                                                             #
    # ------------------------------------------------------------------ #

    def get_comments(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get comments on a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the comments.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/child/comment"
        return self.get(url)

    def add_comment(self, page_id: int, body: str) -> dict | None:
        """
        Add a comment to a page.

        :param page_id: The ID of the page to comment on.
        :type page_id: int
        :param body: The comment body in Confluence storage format.
        :type body: str
        :return: The created comment object.
        :rtype: dict or None
        """
        url = "/rest/api/content"
        payload: dict[str, Any] = {
            "type": "comment",
            "container": {"id": page_id, "type": "page"},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        return self.post(url, json=payload)

    def delete_comment(self, comment_id: int) -> dict | None:
        """
        Delete a comment.

        :param comment_id: The ID of the comment content object.
        :type comment_id: int
        :return: The response from the API.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{comment_id}"
        return self.delete(url)

    # ------------------------------------------------------------------ #
    # Restrictions & discovery                                             #
    # ------------------------------------------------------------------ #

    def get_content_restrictions(self, page_id: int) -> SimpleNamespace | str | None:
        """
        Get restrictions on a page.

        :param page_id: The ID of the page.
        :type page_id: int
        :return: A SimpleNamespace containing the restrictions.
        :rtype: SimpleNamespace or str or None
        """
        url = f"/rest/api/content/{page_id}/restriction"
        return self.get(url)

    def get_content_by_title(
        self, space_key: str, title: str
    ) -> SimpleNamespace | str | None:
        """
        Find a page by title within a space.

        :param space_key: The space key.
        :type space_key: str
        :param title: The exact page title.
        :type title: str
        :return: A SimpleNamespace containing the matching content.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content"
        return self.get(
            url, params={"spaceKey": space_key, "title": title, "type": "page"}
        )

    def search_content_by_label(
        self,
        label: str,
        space_key: str | None = None,
        limit: int = 25,
    ) -> SimpleNamespace | str | None:
        """
        Search pages by label.

        :param label: The label to search for.
        :type label: str
        :param space_key: Restrict search to a space (optional).
        :type space_key: str, optional
        :param limit: Maximum number of results (default 25).
        :type limit: int, optional
        :return: A SimpleNamespace containing the matching content.
        :rtype: SimpleNamespace or str or None
        """
        url = "/rest/api/content"
        params: dict = {"label": label, "type": "page", "limit": limit}
        if space_key:
            params["spaceKey"] = space_key
        return self.get(url, params=params)

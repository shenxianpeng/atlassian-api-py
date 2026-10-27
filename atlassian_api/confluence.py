from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from atlassian_api.client import AtlassianAPI
from atlassian_api.error import APIError, NotFoundError
from atlassian_api.logger import get_logger

logger = get_logger(__name__)

#: Base path of the Confluence Cloud REST API v2 (relative to ``/wiki``).
V2 = "/api/v2"

#: Largest page size Confluence Cloud v2 accepts.
_V2_MAX_LIMIT = 250

_V2_CONTENT_TYPES = ("page", "blogpost")


class Confluence(AtlassianAPI):
    """Client for Confluence REST API operations on Cloud and Server/Data Center.

    Use this class for pages, spaces, content search, child pages, attachments,
    and labels. Read methods return nested ``SimpleNamespace`` objects when the
    API returns JSON, raw text for non-JSON responses, or ``None`` for empty
    responses.

    On Confluence Cloud (detected from a ``*.atlassian.net`` URL, or
    ``cloud=True``) the page, space, comment, label and attachment-listing
    methods use the REST API v2, because Atlassian removed the matching v1
    endpoints from Cloud. ``/wiki`` is appended to the URL when missing. List
    methods keep the v1 shape (``results``, ``start``, ``limit``, ``size``) and
    translate ``start``/``limit`` to v2 cursors. Items themselves are v2
    objects: for example a page has ``spaceId`` instead of ``space.key``.

    .. seealso::
        `Confluence Server REST API <https://docs.atlassian.com/ConfluenceServer/rest/7.17.2/>`_,
        `Confluence Cloud REST API v2 <https://developer.atlassian.com/cloud/confluence/rest/v2/>`_
    """

    def __init__(self, url: str, *args: Any, **kwargs: Any) -> None:
        """Create a Confluence client.

        Accepts the same arguments as :class:`atlassian_api.client.AtlassianAPI`.
        """
        super().__init__(url, *args, **kwargs)
        if self.cloud and not self.url.endswith("/wiki"):
            self.url += "/wiki"
        self._space_ids: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Cloud (REST API v2) helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _next_cursor(response: object) -> str | None:
        """Return the ``cursor`` of the next v2 page, if there is one."""
        next_link = getattr(getattr(response, "_links", None), "next", None)
        if not next_link:
            return None
        return parse_qs(urlsplit(next_link).query).get("cursor", [None])[0]

    def _v2_list(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        start: int = 0,
        limit: int = 25,
        item_type: str | None = None,
    ) -> SimpleNamespace:
        """Read a cursor-paginated v2 list and return a v1-style page.

        :param path: v2 endpoint path.
        :param params: Extra query parameters.
        :param start: Number of matching items to skip.
        :param limit: Maximum number of items to return.
        :param item_type: Keep only items whose ``type`` equals this value.
        :return: ``SimpleNamespace(results, start, limit, size)``.
        """
        query: dict[str, Any] = dict(params or {})
        wanted = start + limit
        query["limit"] = max(1, min(wanted, _V2_MAX_LIMIT))
        results: list = []
        while True:
            response = self.get(path, params=query)
            if not isinstance(response, SimpleNamespace):
                break
            items = getattr(response, "results", None) or []
            if item_type is not None:
                items = [i for i in items if getattr(i, "type", None) == item_type]
            results.extend(items)
            cursor = self._next_cursor(response)
            if len(results) >= wanted or not cursor:
                break
            query["cursor"] = cursor
        page = results[start:wanted]
        return SimpleNamespace(results=page, start=start, limit=limit, size=len(page))

    def _space(self, space_key: str) -> SimpleNamespace:
        """Return the v2 space object for a space key."""
        response = self.get(f"{V2}/spaces", params={"keys": space_key})
        results = getattr(response, "results", None) or []
        if not results:
            raise APIError(404, f"Space {space_key!r} not found")
        space = results[0]
        self._space_ids[space_key] = space.id
        return space

    def _space_id(self, space_key: str) -> str:
        """Return (and cache) the v2 space ID for a space key."""
        if space_key not in self._space_ids:
            self._space(space_key)
        return self._space_ids[space_key]

    @staticmethod
    def _v2_collection(content_type: str) -> str:
        """Return the v2 collection name for a v1 content type."""
        if content_type not in _V2_CONTENT_TYPES:
            raise ValueError(
                f"Content type {content_type!r} is not supported on Confluence "
                f"Cloud; use one of {', '.join(_V2_CONTENT_TYPES)}."
            )
        return f"{content_type}s"

    @staticmethod
    def _storage(value: str) -> dict[str, str]:
        """Return a v2 body in storage representation."""
        return {"representation": "storage", "value": value}

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def get_content(self) -> SimpleNamespace | str | None:
        """Return content (pages) visible to the current user.

        :return: Content data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self._v2_list(f"{V2}/pages", params={"status": "current"})
        url = "/rest/api/content"
        return self.get(url)

    def create_content(
        self,
        title: str,
        space_key: str,
        body_value: str,
        ancestors_id: int | str | None = None,
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
        :type ancestors_id: int or str, optional
        :param type: Content type, for example ``page``. Cloud supports
            ``page`` and ``blogpost``.
        :type type: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        if self.cloud:
            collection = self._v2_collection(type)
            payload: dict[str, Any] = {
                "spaceId": self._space_id(space_key),
                "status": "current",
                "title": title,
                "body": self._storage(body_value),
            }
            if ancestors_id is not None:
                payload["parentId"] = str(ancestors_id)
            return self.post(f"{V2}/{collection}", json=payload)
        url = "/rest/api/content"
        payload = {
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
        page_id: int | str,
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
        :type page_id: int or str
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
        if self.cloud:
            url = f"{V2}/{self._v2_collection(type)}/{page_id}"
            current_params: dict[str, Any] | None = None
        else:
            url = f"/rest/api/content/{page_id}"
            current_params = {"expand": "version"}
        if version is None:
            current = self.get(url, params=current_params)
            if isinstance(current, SimpleNamespace):
                version = current.version.number + 1
            else:
                version = 1
        if self.cloud:
            json: dict[str, Any] = {
                "id": str(page_id),
                "status": "current",
                "title": title,
                "body": self._storage(body_value),
                "version": {"number": version},
            }
            return self.put(url, json=json)
        json = {
            "version": {"number": version},
            "title": f"{title}",
            "type": f"{type}",
            "body": {
                "storage": {"value": f"{body_value}", "representation": "storage"}
            },
        }
        return self.put(url, json=json)

    def delete_content(self, page_id: int | str, type: str = "page") -> dict | None:
        """Delete content from Confluence by content ID.

        :param page_id: The ID of the content to delete.
        :type page_id: int or str
        :param type: Content type. Only used on Cloud, where pages and blog
            posts have separate endpoints.
        :type type: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        if self.cloud:
            return self.delete(f"{V2}/{self._v2_collection(type)}/{page_id}")
        url = f"/rest/api/content/{page_id}"
        return self.delete(url)

    def get_content_by_id(self, page_id: int | str) -> SimpleNamespace | str | None:
        """Return content by content ID.

        On Cloud the page body is included in storage format
        (``body.storage.value``).

        :param page_id: The ID of the content to retrieve.
        :type page_id: int or str
        :return: Content data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self.get(f"{V2}/pages/{page_id}", params={"body-format": "storage"})
        url = f"/rest/api/content/{page_id}"
        return self.get(url)

    def get_content_history(self, page_id: int | str) -> SimpleNamespace | str | None:
        """Return version history for a content item.

        On Cloud this is the v2 version list (``results`` of versions).

        :param page_id: The ID of the content to retrieve the history for.
        :type page_id: int or str
        :return: History data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self.get(f"{V2}/pages/{page_id}/versions")
        url = f"/rest/api/content/{page_id}/history"
        return self.get(url)

    # ------------------------------------------------------------------
    # Spaces
    # ------------------------------------------------------------------

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
        if self.cloud:
            return self._v2_list(f"{V2}/spaces", start=start, limit=limit)
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
        :raises APIError: On Cloud, with code 404 when no space has this key.
        """
        if self.cloud:
            return self._space(space_key)
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
        if self.cloud:
            collection = self._v2_collection(content_type)
            space_id = self._space_id(space_key)
            # v2 lists archived pages too unless asked for current ones.
            return self._v2_list(
                f"{V2}/spaces/{space_id}/{collection}",
                params={"status": "current"},
                start=start,
                limit=limit,
            )
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
        if self.cloud:
            # Cloud ignores ``start`` here and pages with cursors instead.
            return self._v2_list(url, params={"cql": cql}, start=start, limit=limit)
        params: dict[str, Any] = {"cql": cql, "start": start, "limit": limit}
        return self.get(url, params=params)

    def get_child_pages(
        self, page_id: int | str, start: int = 0, limit: int = 25
    ) -> SimpleNamespace | str | None:
        """Return child pages for a parent page.

        :param page_id: The ID of the parent page.
        :type page_id: int or str
        :param start: The starting index for pagination (default 0).
        :type start: int, optional
        :param limit: The maximum number of results to return (default 25).
        :type limit: int, optional
        :return: Child page data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            # direct-children also lists whiteboards, databases and folders.
            return self._v2_list(
                f"{V2}/pages/{page_id}/direct-children",
                start=start,
                limit=limit,
                item_type="page",
            )
        url = f"/rest/api/content/{page_id}/child/page"
        params: dict[str, Any] = {"start": start, "limit": limit}
        return self.get(url, params=params)

    # ------------------------------------------------------------------
    # Attachments, labels, comments
    # ------------------------------------------------------------------

    def get_attachments(self, page_id: int | str) -> SimpleNamespace | str | None:
        """Return attachments for a page.

        :param page_id: The ID of the page.
        :type page_id: int or str
        :return: Attachment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self._v2_list(f"{V2}/pages/{page_id}/attachments", limit=50)
        url = f"/rest/api/content/{page_id}/child/attachment"
        return self.get(url)

    def get_labels(self, page_id: int | str) -> SimpleNamespace | str | None:
        """Return labels for a content item.

        :param page_id: The ID of the content.
        :type page_id: int or str
        :return: Label data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self._v2_list(f"{V2}/pages/{page_id}/labels")
        url = f"/rest/api/content/{page_id}/label"
        return self.get(url)

    def add_label(self, page_id: int | str, label: str) -> dict | None:
        """Add a global label to a content item.

        :param page_id: The ID of the content.
        :type page_id: int or str
        :param label: The label name to add.
        :type label: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        url = f"/rest/api/content/{page_id}/label"
        payload = [{"prefix": "global", "name": label}]
        return self.post(url, json=payload)

    def remove_label(self, page_id: int | str, label: str) -> dict | None:
        """Remove a label from a content item.

        :param page_id: The ID of the content.
        :type page_id: int or str
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
        :return: Content data for the matching page (in ``results``), raw
            response text for non-JSON responses, or ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            params: dict[str, Any] = {
                "space-id": self._space_id(space_key),
                "title": title,
                "status": "current",
                "body-format": "storage",
            }
            return self._v2_list(f"{V2}/pages", params=params)
        url = "/rest/api/content"
        params = {
            "spaceKey": space_key,
            "title": title,
            "type": "page",
        }
        return self.get(url, params=params)

    def upload_attachment(
        self,
        page_id: int | str,
        filename: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict | None:
        """Upload a file as an attachment to a page.

        :param page_id: The ID of the page to attach the file to.
        :type page_id: int or str
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
        url = f"/rest/api/content/{page_id}/child/attachment"
        response = self.request(
            "POST",
            url,
            files={"file": (filename, file_data, content_type)},
            data={"comment": ""},
            # CSRF bypass, sent with this request only.
            headers={"X-Atlassian-Token": "nocheck"},
        )
        return self._response_handler(response)

    def get_comments(self, page_id: int | str) -> SimpleNamespace | str | None:
        """Return comments for a page.

        :param page_id: The ID of the page.
        :type page_id: int or str
        :return: Comment data, raw response text for non-JSON responses, or
            ``None`` for an empty body.
        :rtype: SimpleNamespace or str or None
        """
        if self.cloud:
            return self._v2_list(
                f"{V2}/pages/{page_id}/footer-comments",
                params={"body-format": "storage"},
            )
        url = f"/rest/api/content/{page_id}/child/comment"
        return self.get(url)

    def add_comment(self, page_id: int | str, body: str) -> dict | None:
        """Add a comment to a page.

        :param page_id: The ID of the page to comment on.
        :type page_id: int or str
        :param body: Comment body in Confluence storage format.
        :type body: str
        :return: Decoded API response, or ``None`` when Confluence returns no body.
        :rtype: dict or None
        """
        if self.cloud:
            payload: dict[str, Any] = {
                "pageId": str(page_id),
                "body": self._storage(body),
            }
            return self.post(f"{V2}/footer-comments", json=payload)
        url = "/rest/api/content"
        payload = {
            "type": "comment",
            "container": {"id": page_id, "type": "page"},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        return self.post(url, json=payload)

    # ------------------------------------------------------------------
    # Higher-level helpers
    # ------------------------------------------------------------------

    def iter_search(self, cql: str, page_size: int = 50) -> Iterator[SimpleNamespace]:
        """Yield every result of a CQL search, following ``_links.next``.

        Works on Server/Data Center (``start`` paging) and Cloud (cursor
        paging).

        .. code-block:: python

            for page in confluence.iter_search('space = DOC and type = page'):
                print(page.id, page.title)

        :param cql: The CQL query string.
        :type cql: str
        :param page_size: Results requested per API call.
        :type page_size: int, optional
        :return: Content results.
        :rtype: Iterator[SimpleNamespace]
        """
        params: dict[str, Any] = {"cql": cql, "limit": page_size}
        while True:
            response = self.get("/rest/api/content/search", params=params)
            if not isinstance(response, SimpleNamespace):
                return
            results = getattr(response, "results", None) or []
            yield from results
            next_link = getattr(getattr(response, "_links", None), "next", None)
            if not results or not next_link:
                return
            query = parse_qs(urlsplit(next_link).query)
            moved = False
            for key in ("start", "cursor"):
                if key in query:
                    params[key] = query[key][0]
                    moved = True
            if not moved:
                return

    def create_or_update_page(
        self,
        space_key: str,
        title: str,
        body_value: str,
        parent_id: int | str | None = None,
    ) -> dict | None:
        """Create a page, or update it if a page with this title exists.

        Handy for publishing generated reports: run the same script every
        time and the page is created once, then updated.

        :param space_key: The key of the space.
        :type space_key: str
        :param title: The exact page title.
        :type title: str
        :param body_value: Body content in Confluence storage format.
        :type body_value: str
        :param parent_id: Parent page for a new page. An existing page is not
            moved.
        :type parent_id: int or str, optional
        :return: The created or updated page.
        :rtype: dict or None
        """
        existing = self.get_page_by_title(space_key, title)
        results = getattr(existing, "results", None) or []
        if results:
            return self.update_content(results[0].id, title, body_value)
        return self.create_content(title, space_key, body_value, ancestors_id=parent_id)

    def download_attachment(
        self,
        page_id: int | str,
        filename: str,
        path: str | Path | None = None,
    ) -> bytes | Path:
        """Download a page attachment by file name.

        :param page_id: The ID of the page.
        :type page_id: int or str
        :param filename: The attachment's file name.
        :type filename: str
        :param path: Where to write the file. The download is streamed to disk
            in chunks, so large files are not held in memory.
        :type path: str or pathlib.Path, optional
        :return: The file contents, or ``path`` when one was given.
        :rtype: bytes or pathlib.Path
        :raises NotFoundError: If the page has no attachment with this name.
        """
        params = {"filename": filename}
        if self.cloud:
            listing = self.get(f"{V2}/pages/{page_id}/attachments", params=params)
        else:
            listing = self.get(
                f"/rest/api/content/{page_id}/child/attachment", params=params
            )
        results = getattr(listing, "results", None) or []
        if not results:
            raise NotFoundError(
                404, f"Page {page_id} has no attachment named {filename!r}"
            )
        attachment = results[0]
        if self.cloud:
            link = getattr(attachment, "downloadLink", None)
        else:
            link = getattr(getattr(attachment, "_links", None), "download", None)
        if not link:
            raise APIError(None, f"Attachment {filename!r} has no download link")
        media = str(
            getattr(attachment, "mediaType", None)
            or getattr(getattr(attachment, "extensions", None), "mediaType", None)
            or ""
        )
        # A login page instead of a non-HTML file is an error, not the file.
        return self._download(
            link, path, reject_html=bool(media) and not media.startswith("text/html")
        )

    def export_page_pdf(
        self, page_id: int | str, path: str | Path | None = None
    ) -> bytes | Path:
        """Export a page as PDF (Server/Data Center).

        :param page_id: The ID of the page.
        :type page_id: int or str
        :param path: Where to write the PDF. When omitted, the bytes are
            returned.
        :type path: str or pathlib.Path, optional
        :return: The PDF contents, or ``path`` when one was given.
        :rtype: bytes or pathlib.Path
        :raises NotImplementedError: On Cloud, which has no REST endpoint for
            PDF export.
        """
        if self.cloud:
            raise NotImplementedError(
                "Confluence Cloud has no REST API for PDF export; use the "
                "page's Export to PDF action in the browser."
            )
        return self._download(
            "/spaces/flyingpdf/pdfpageexport.action",
            path,
            params={"pageId": page_id},
            reject_html=True,
        )

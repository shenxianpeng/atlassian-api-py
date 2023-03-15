from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

from types import SimpleNamespace

logger = get_logger(__name__)


class Confluence(AtlassianAPI):
    """
    Confluence API Reference
    https://docs.atlassian.com/ConfluenceServer/rest/7.17.2/
    """

    def get_content(self) -> SimpleNamespace:
        """Get content"""
        url = "/rest/api/content"
        return self.get(url) or {}

    def create_content(
        self, title, space_key, body_value, ancestors_id=None, type="page"
    ) -> dict:
        """Create content"""
        url = "/rest/api/content"
        json = {
            "type": f"{type}",
            "title": f"{title}",
            "space": {"key": f"{space_key}"},
            "body": {
                "storage": {"value": f"{body_value}", "representation": "storage"}
            },
        }
        if ancestors_id:
            json = {
                "type": f"{type}",
                "title": f"{title}",
                "ancestors": [{"id": ancestors_id}],
                "space": {"key": f"{space_key}"},
                "body": {
                    "storage": {"value": f"{body_value}", "representation": "storage"}
                },
            }
        return self.post(url, json=json) or {}

    def update_content(self, page_id, title, body_value, type="page") -> dict:
        url = f"/rest/api/content/{page_id}"
        json = {
            "version": {"number": 2},
            "title": f"{title}",
            "type": f"{type}",
            "body": {
                "storage": {"value": f"{body_value}", "representation": "storage"}
            },
        }
        return self.put(url, json=json) or {}

    def delete_content(self, page_id) -> None:
        url = f"/rest/api/content/{page_id}"
        return self.delete(url) or {}

    def get_content_by_id(self, page_id) -> SimpleNamespace:
        url = f"/rest/api/content/{page_id}"
        return self.get(url) or {}

    def get_content_history(self, page_id) -> SimpleNamespace:
        url = f"/rest/api/content/{page_id}/history"
        return self.get(url) or {}

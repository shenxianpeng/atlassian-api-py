from atlassian.client import AtlassianAPI
from atlassian.logger import get_logger

logger = get_logger(__name__)

class Confluence(AtlassianAPI):
    """
    Confluence API Reference
    https://docs.atlassian.com/ConfluenceServer/rest/7.17.2/
    """
    def get_content(self):
        """Get content"""
        url = f"/rest/api/content"
        return self.get(url) or {}

    def get_content_by_id(self, id):
        """Get content"""
        url = f"/rest/api/content/{id}"
        return self.get(url) or {}

    def create_content(self, title, space_key):
        """Create content"""
        url = f"/rest/api/content"
        body = {
            "type": "page",
            "status": "current",
            "title": f"{title}",
            "space":{"key":f"{space_key}"},
        }
        return self.post(url, json=body) or {}


    def update_content(self):
        pass

    def delete_content(self):
        pass


    def get_content_history(self):
        pass
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

    def create_content():
        pass

    def update_content():
        pass

    def delete_content():
        pass

    def get_content_by_id():
        pass

    def get_content_history():
        pass
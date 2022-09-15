import unittest
from atlassian import Confluence

wiki_url = os.getenv('CONFLUENCE_URL')
wiki_usr = os.getenv('CONFLUENCE_USR')
wiki_psw = os.getenv('CONFLUENCE_PSW')


class TestConfluence(unittest.TestCase):
    """Confluence Test Cases"""

    def setUp(self):
        """Set connection with Confluence"""
        self.wiki = Confluence(url=wiki_url, username=wiki_usr, password=wiki_psw)

    def test_get_content(self):
        content = self.wiki.get_content()
        limit = content.limit
        assert(limit, 25)

    def test_operate_content(self):
        # test create_content
        response = self.wiki.create_content(
            title="My Test Page", 
            ancestors_id='368913434',
            space_key="~blwmv",
            body_value="<p>This is a new page</p>")
        assert(response['status'], "current")

        # test update_content
        page_id = response['id']
        a = self.wiki.update_content(page_id, title="My Test Page Update", body_value="<p>This is a update page</p>")
        
        # test get_content_by_id
        page_content = self.wiki.get_content_by_id(page_id)
        assert(page_content.title, "My Test Page Update")

        # test get_content_history
        page_history = self.wiki.get_content_history(page_id)
        assert(page_history.latest, 'true')

        # test delete_content
        self.wiki.delete_content(page_id)
        page_content = self.wiki.get_content_by_id(page_id)
        assert(page_content.statusCode, 404)

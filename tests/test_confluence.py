import unittest
import configparser
from atlassian import Confluence

config = configparser.ConfigParser()
config.read("config.ini")

wiki_url = config["confluence"]["url"]
wiki_usr = config["confluence"]["username"]
wiki_psw = config["confluence"]["password"]


class TestConfluence(unittest.TestCase):
    """Confluence Test Cases"""
    def setUp(self):
        """Set connection with Confluence"""
        print("hello from wiki")
        self.wiki = Confluence(url=wiki_url, username=wiki_usr, password=wiki_psw)
        print("hello from wiki")

    def test_get_content(self):
        content = self.wiki.get_content()
        print("hello from wiki")

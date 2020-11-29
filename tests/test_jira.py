import unittest
from atlassian import Jira


class TestJira(unittest.TestCase):

    def setUp(self):
        self.jira = Jira(url='https://jira.rocketsoftware.com', username='username', password='password')

    def test_get_status(self):
        status = self.jira.get_status('MVQA-901')
        self.assertEqual(status, 'Open')

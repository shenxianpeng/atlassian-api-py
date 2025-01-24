import unittest
from unittest.mock import MagicMock
from atlassian.bitbucket import Bitbucket


class TestBitbucketGetPaged(unittest.TestCase):
    def setUp(self):
        self.bitbucket = Bitbucket("https://fake_url")
        self.bitbucket.get = MagicMock()

    def test_no_pagination(self):
        response = MagicMock(values=[1, 2, 3], isLastPage=True)
        self.bitbucket.get.return_value = response
        result = self.bitbucket._get_paged("url", {})
        self.assertEqual(result, [1, 2, 3])

    def test_pagination(self):
        response1 = MagicMock(values=[1, 2, 3], isLastPage=False, nextPageStart=4)
        response2 = MagicMock(values=[4, 5, 6], isLastPage=True)
        self.bitbucket.get.side_effect = [response1, response2]
        result = self.bitbucket._get_paged("url", {})
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])

    def test_limit_parameter(self):
        response1 = MagicMock(values=[1, 2, 3], isLastPage=False, nextPageStart=4)
        response2 = MagicMock(values=[4, 5, 6], isLastPage=True)
        self.bitbucket.get.side_effect = [response1, response2]
        result = self.bitbucket._get_paged("url", {"limit": 6})
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])

    def test_limit_parameter_set_to_0(self):
        response = MagicMock(values=[1, 2, 3], isLastPage=True)
        self.bitbucket.get.return_value = response
        result = self.bitbucket._get_paged("url", {"limit": 0})
        self.assertEqual(result, [1, 2, 3])

    def test_response_having_no_values(self):
        response = MagicMock(values=None, isLastPage=True)
        self.bitbucket.get.return_value = response
        result = self.bitbucket._get_paged("url", {})
        self.assertEqual(result, [])

    def test_response_having_isLastPage_set_to_True(self):
        response = MagicMock(values=[1, 2, 3], isLastPage=True)
        self.bitbucket.get.return_value = response
        result = self.bitbucket._get_paged("url", {})
        self.assertEqual(result, [1, 2, 3])

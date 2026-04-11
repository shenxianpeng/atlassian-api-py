"""Convenience imports for the Atlassian product clients.

Import ``Jira``, ``Bitbucket``, and ``Confluence`` from this package instead of
their individual modules when writing scripts.

Example:

.. code-block:: python

    from atlassian import Jira, Bitbucket, Confluence

    jira = Jira(url="https://jira.company.com", token="your_token")
    bitbucket = Bitbucket(url="https://bitbucket.company.com", token="your_token")
    confluence = Confluence(url="https://confluence.company.com", token="your_token")
"""

from importlib.metadata import PackageNotFoundError, version

from atlassian.jira import Jira
from atlassian.bitbucket import Bitbucket
from atlassian.confluence import Confluence

try:
    __version__ = version("atlassian-api-py")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["Jira", "Bitbucket", "Confluence", "__version__"]

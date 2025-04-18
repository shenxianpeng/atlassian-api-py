"""
Atlassian API Library

This module provides access to the main classes for interacting with Atlassian products.

Available classes:

* Jira: For interacting with Jira APIs.
* Bitbucket: For interacting with Bitbucket APIs.
* Confluence: For interacting with Confluence APIs.

.. note::
    Import these classes directly from this module for convenience.

Example usage:

.. code-block:: python

    from atlassian import Jira, Bitbucket, Confluence

    jira = Jira(url="https://your-jira-instance.com", username="user", password="pass")
    bitbucket = Bitbucket(url="https://your-bitbucket-instance.com", token="your-token")
    confluence = Confluence(url="https://your-confluence-instance.com", username="user", password="pass")
"""

from atlassian.jira import Jira
from atlassian.bitbucket import Bitbucket
from atlassian.confluence import Confluence

__all__ = ["Jira", "Bitbucket", "Confluence"]

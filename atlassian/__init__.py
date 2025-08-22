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

    jira = Jira(url="https://jira.company.com", username="your_username", password="your_password")
    bitbucket = Bitbucket(url="https://bitbucket.company.com", token="your_token")
    confluence = Confluence(url="https://confluence.company.com", username="your_username", password="your_password")
"""

from atlassian.jira import Jira
from atlassian.bitbucket import Bitbucket
from atlassian.confluence import Confluence

__all__ = ["Jira", "Bitbucket", "Confluence"]

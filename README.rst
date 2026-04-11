Python Wrapper for Atlassian REST API
=====================================

.. start-overview

.. |pypi-version| image:: https://img.shields.io/pypi/v/atlassian-api-py
   :target: https://pypi.org/project/atlassian-api-py/
   :alt: PyPI

.. |docs-badge| image:: https://readthedocs.org/projects/atlassian-api-py/badge/?version=latest
   :target: https://atlassian-api-py.readthedocs.io/
   :alt: Documentation

.. |coverage-badge| image:: https://codecov.io/gh/shenxianpeng/atlassian-api-py/branch/main/graph/badge.svg?token=UE90982FF2
   :target: https://codecov.io/gh/shenxianpeng/atlassian-api-py
   :alt: Code Coverage

.. |python-version| image:: https://img.shields.io/pypi/pyversions/atlassian-api-py?style=flat-square
   :target: https://pypi.org/project/atlassian-api-py
   :alt: PyPI - Python Version

.. |sonar-badge| image:: https://sonarcloud.io/api/project_badges/measure?project=shenxianpeng_atlassian-api-py&metric=alert_status
   :target: https://sonarcloud.io/summary/new_code?id=shenxianpeng_atlassian-api-py
   :alt: Quality Gate Status

.. |downloads-badge| image:: https://img.shields.io/pypi/dw/atlassian-api-py
   :alt: PyPI - Downloads

.. |commit-check-badge| image:: https://img.shields.io/badge/commit--check-enabled-brightgreen?logo=Git&logoColor=white
   :target: https://github.com/commit-check/commit-check
   :alt: Commit Check


|pypi-version| |docs-badge| |coverage-badge| |python-version| |commit-check-badge|

Overview
--------

``atlassian-api-py`` is a small Python wrapper for Atlassian REST APIs.
It provides ready-to-use clients for Jira, Bitbucket, and Confluence so you
can automate common Atlassian tasks without rewriting endpoint and session
handling code.

The clients are intentionally lightweight:

* ``GET`` helpers return nested ``SimpleNamespace`` objects, so response fields
  can be accessed with dot notation.
* ``POST``, ``PUT``, and ``DELETE`` helpers return decoded JSON dictionaries
  when the API returns JSON, or ``None`` for empty responses.
* HTTP ``4xx`` and ``5xx`` responses raise ``APIError`` with the status code
  and response body.

Documentation: `atlassian-api-py.readthedocs.io <https://atlassian-api-py.readthedocs.io/>`_

.. end-overview

.. start-install

Installation
------------

Python 3.9 or newer is required.

Install from PyPI:

.. code-block:: bash

   pip install atlassian-api-py

Upgrade an existing installation:

.. code-block:: bash

   pip install --upgrade atlassian-api-py

.. end-install

Quick Start
-----------

Create a client for the Atlassian product you want to automate, then call the
method that matches the operation.

.. code-block:: python

   from atlassian import Jira

   jira = Jira(
       url="https://jira.company.com",
       username="your_username",
       password="your_password",
   )

   issue = jira.issue("TEST-1")
   print(f"{issue.key}: {issue.fields.summary}")

Use a token instead of username/password when your Atlassian instance supports
bearer token authentication:

.. code-block:: python

   from atlassian import Jira

   jira = Jira(url="https://jira.company.com", token="your_token")

Usage
-----

You can authenticate with username/password or a token. Pass only the
credential type supported by your Atlassian instance.

Using username and password
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Jira

   jira = Jira(
       url="https://jira.company.com",
       username="your_username",
       password="your_password",
   )

Using a token
~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Jira

   jira = Jira(url="https://jira.company.com", token="your_token")

Loading credentials from a file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For scripts, keep credentials outside your source code. One simple option is a
local ``config.ini`` file that is excluded from version control.

.. code-block:: ini

   [jira]
   url = https://jira.company.com
   username = your_username
   password = your_password
   # Alternatively
   token = your_token

.. code-block:: python

   import configparser

   from atlassian import Jira

   config = configparser.ConfigParser()
   config.read('config.ini')
   section = config["jira"]

   jira = Jira(
       url=section["url"],
       username=section.get("username"),
       password=section.get("password"),
       token=section.get("token"),
   )

Common Jira tasks
~~~~~~~~~~~~~~~~~

Read issue fields:

.. code-block:: python

   issue = jira.issue("TEST-1")
   print(issue.fields.status.name)      # e.g. "Triage"
   print(issue.fields.description)      # e.g. "This is a demo Jira ticket"
   print(issue.fields.issuetype.name)   # e.g. "Bug"

Update an issue:

.. code-block:: python

   jira.update_issue_label("TEST-1", add_labels=["automation"])
   jira.add_issue_comment("TEST-1", "Checked by an automation script.")

Create an issue:

.. code-block:: python

   jira.create_issue(
       fields={
           "project": {"key": "TEST"},
           "summary": "Created from atlassian-api-py",
           "issuetype": {"name": "Task"},
           "description": "This issue was created through the Jira REST API.",
       }
   )

Common Bitbucket tasks
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Bitbucket

   bitbucket = Bitbucket(
       url="https://bitbucket.company.com",
       username="your_username",
       password="your_password",
   )

   repos = bitbucket.get_project_repo("PROJECT_KEY")
   for repo in repos:
       print(repo.name)

   bitbucket.create_pull_request(
       project_key="PROJECT_KEY",
       repo_slug="repo_slug",
       title="Add automation update",
       from_branch="feature/automation",
       to_branch="main",
       reviewers=["reviewer_slug"],
   )

Common Confluence tasks
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Confluence

   confluence = Confluence(
       url="https://confluence.company.com",
       username="your_username",
       password="your_password",
   )

   page = confluence.get_content_by_id(123456)
   print(page.title)

   confluence.create_content(
       title="Automation Notes",
       space_key="SPACE",
       body_value="<p>Created from atlassian-api-py.</p>",
   )

Response handling
~~~~~~~~~~~~~~~~~

``GET`` responses are parsed into nested ``SimpleNamespace`` objects when the
response body contains JSON:

.. code-block:: python

   issue = jira.issue("TEST-1")
   print(issue.fields.status.name)

If a response body is not JSON, the raw response text is returned. Empty
responses return ``None``. Mutating methods such as ``post()``, ``put()``, and
``delete()`` return a decoded dictionary when JSON is available.

Use ``APIError`` to handle unsuccessful HTTP responses:

.. code-block:: python

   from atlassian.error import APIError

   try:
       jira.issue("MISSING-1")
   except APIError as exc:
       print(exc.code)
       print(exc.message)

More Jira, Bitbucket, and Confluence examples are available in the
`documentation <https://atlassian-api-py.readthedocs.io/>`_.

.. start-license

License
-------

This project is released under the `MIT License <LICENSE>`_.

.. end-license

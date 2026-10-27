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

.. |python-version| image:: https://img.shields.io/pypi/pyversions/atlassian-api-py
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

* **One script for Data Center and Cloud.** Jira and Confluence clients detect
  Atlassian Cloud from the URL (``*.atlassian.net``) and switch to the Cloud
  endpoints where they differ: Jira's ``/search/jql`` with ``nextPageToken``
  paging, ``accountId`` instead of usernames, and the Confluence REST API v2.
  Method names and arguments stay the same; returned items are Cloud objects
  (for example a Confluence page has ``spaceId`` instead of ``space.key``).
* **Installs next to** ``atlassian-python-api``. The import package is
  ``atlassian_api``, so both libraries can live in the same environment.
* **One runtime dependency** (``requests``) and inline type hints.
* Bitbucket support targets Bitbucket Server/Data Center.

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

   from atlassian_api import Jira

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

   from atlassian_api import Jira

   jira = Jira(url="https://jira.company.com", token="your_token")

Atlassian Cloud
~~~~~~~~~~~~~~~

Use your account email and an
`API token <https://id.atlassian.com/manage-profile/security/api-tokens>`_
as username and password. The same methods work as on Data Center:

.. code-block:: python

   from atlassian_api import Confluence, Jira

   jira = Jira(
       url="https://your-site.atlassian.net",
       username="you@example.com",
       password="your_api_token",
   )
   issues = jira.search_issue_with_jql("project = TEST AND status = Open")

   confluence = Confluence(
       url="https://your-site.atlassian.net",  # "/wiki" is added for you
       username="you@example.com",
       password="your_api_token",
   )
   page = confluence.get_page_by_title("SPACE", "Release notes")

Cloud identifies users by ``accountId``: pass it wherever a method takes a
username (``assign_issue``, ``add_issue_watcher``, ``user``). For a site on a
custom domain, pass ``cloud=True``.

Upgrading from 1.x
~~~~~~~~~~~~~~~~~~

2.0 renames the import package from ``atlassian`` to ``atlassian_api``, because
``atlassian-python-api`` also installs a package named ``atlassian`` and the
two overwrote each other. Update your imports:

.. code-block:: python

   # 1.x
   from atlassian import Jira
   from atlassian.error import APIError

   # 2.x
   from atlassian_api import Jira
   from atlassian_api.error import APIError

If ``atlassian-python-api`` is installed in the same environment, reinstall it
after upgrading. Uninstalling 1.x removes the ``atlassian`` files the two
packages shared:

.. code-block:: bash

   pip install --upgrade atlassian-api-py
   pip install --force-reinstall --no-deps atlassian-python-api

The deprecated ``Jira.create_task()`` and ``Jira.create_sub_task()`` are
removed; use ``Jira.create_issue()``. See the
`changelog <https://atlassian-api-py.readthedocs.io/en/latest/changelog.html>`_
for the full list.

Usage
-----

You can authenticate with username/password or a token. Pass only the
credential type supported by your Atlassian instance.

Using username and password
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from atlassian_api import Jira

   jira = Jira(
       url="https://jira.company.com",
       username="your_username",
       password="your_password",
   )

Using a token
~~~~~~~~~~~~~

.. code-block:: python

   from atlassian_api import Jira

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

   from atlassian_api import Jira

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

   from atlassian_api import Bitbucket

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

   from atlassian_api import Confluence

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

   from atlassian_api.error import APIError

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

atlassian-api-py
================

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

``atlassian-api-py`` is a Python client for the Jira, Confluence and Bitbucket
REST APIs, written for scripts that have to keep working on both Atlassian
Data Center and Atlassian Cloud.

.. code-block:: python

   from atlassian_api import Jira

   # Data Center: a personal access token
   jira = Jira(url="https://jira.company.com", token="personal-access-token")
   # Cloud: the same code, with your account email and an API token
   # jira = Jira(url="https://your-site.atlassian.net",
   #             username="you@example.com", password="api-token")

   issue = jira.issue("TEST-1")
   print(issue.key, issue.fields.summary)

   for found in jira.iter_issues("project = TEST AND status = Open", fields=["summary"]):
       print(found["key"], found["fields"]["summary"])

Use it when
~~~~~~~~~~~

* **The same script has to run on Data Center and Cloud.** The Jira and
  Confluence clients detect Cloud from the URL (``*.atlassian.net``,
  ``*.jira.com``, ``api.atlassian.com``) and switch to the Cloud endpoints
  where the two differ: Jira's ``/search/jql`` with ``nextPageToken`` paging,
  ``accountId`` instead of usernames, and the Confluence REST API v2. Method
  names and arguments stay the same; returned items are what each deployment
  sends (a Confluence page has ``spaceId`` on Cloud instead of ``space.key``).
* **atlassian-python-api is already installed, or might be.** The import
  package is ``atlassian_api``, so both libraries live in one environment.
  `Coming from atlassian-python-api <https://atlassian-api-py.readthedocs.io/en/latest/migration.html>`_
  maps its methods to this library's and lists what is missing here.
* **You want failures you can handle.** Each HTTP error raises a subclass of
  ``APIError`` (``NotFoundError``, ``AuthenticationError``, ``RateLimitError``
  and so on). HTTP 429 is retried and ``Retry-After`` is honoured. A login page
  served by an SSO proxy raises an error instead of being returned as data, and
  a request to an absolute URL on another host is refused, so credentials are
  not sent there.
* **You want a small dependency.** ``requests`` is the only one, and the code
  has inline type hints.

It covers the common Jira operations including Jira Software boards, sprints
and epics, Confluence pages, spaces, attachments and search, and Bitbucket
Server/Data Center repositories, branches, pull requests and permissions.

Use something else when
~~~~~~~~~~~~~~~~~~~~~~~

* You need **Bitbucket Cloud**, **Jira Service Management**, Bamboo, Crowd or
  Xray. `atlassian-python-api <https://github.com/atlassian-api/atlassian-python-api>`_
  covers them, and can be installed next to this library.
* You need an **async** client. This one is synchronous
  (`#128 <https://github.com/shenxianpeng/atlassian-api-py/issues/128>`_).
* You are on **Python 3.9** or older.

What you get back
~~~~~~~~~~~~~~~~~

* Read methods return nested ``SimpleNamespace`` objects, so response fields
  are attributes: ``issue.fields.status.name``.
* Methods that create, update or delete return the decoded JSON as a
  dictionary, or ``None`` for an empty response. JQL searches return issues as
  dictionaries.
* HTTP ``4xx`` and ``5xx`` responses raise ``APIError`` or one of its
  subclasses, with the status code and the response body.

How it is checked
~~~~~~~~~~~~~~~~~

Every line and branch of the library is covered by tests, and CI fails below
100%. The requests sent to Atlassian Cloud follow Atlassian's published
OpenAPI specifications.

For AI coding assistants
~~~~~~~~~~~~~~~~~~~~~~~~

If you are an assistant writing code with this library, or a person using
one: the import package is ``atlassian_api``, and the method names are not
those of ``atlassian-python-api`` or the ``jira`` package. Calling one of
their names raises ``AttributeError`` with the method to use instead.
`llms.txt <https://atlassian-api-py.readthedocs.io/llms.txt>`_ has the facts
to get right, and
`llms-full.txt <https://atlassian-api-py.readthedocs.io/llms-full.txt>`_ has
every method with its signature in one file.

Documentation: `atlassian-api-py.readthedocs.io <https://atlassian-api-py.readthedocs.io/>`_

.. end-overview

.. start-install

Installation
------------

Python 3.10 or newer is required (tested on 3.10 to 3.15).

Install from PyPI:

.. code-block:: bash

   pip install atlassian-api-py

Upgrade an existing installation:

.. code-block:: bash

   pip install --upgrade atlassian-api-py

.. end-install

Creating a Client
-----------------

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

Report on the active sprint of a board, then move issues into the next one:

.. code-block:: python

   board = jira.get_boards(project="TEST", board_type="scrum")[0]
   sprint = jira.get_board_sprints(board.id, state="active")[0]
   for issue in jira.iter_sprint_issues(sprint.id, fields=["summary", "status"]):
       print(issue.key, issue.fields.status.name, issue.fields.summary)

   next_sprint = jira.get_board_sprints(board.id, state="future")[0]
   jira.move_issues_to_sprint(next_sprint.id, ["TEST-7", "TEST-8"])

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
``delete()`` return a decoded dictionary when JSON is available. An HTML page
where JSON was expected (typically a login or SSO redirect) raises ``APIError``
instead of being returned as text.

Errors raise a subclass of ``APIError`` that matches the status code, so you
can catch only what you expect:

.. code-block:: python

   from atlassian_api.error import APIError, NotFoundError

   try:
       jira.issue("MISSING-1")
   except NotFoundError:
       print("no such issue")
   except APIError as exc:          # everything else: 401, 403, 409, 429, 5xx
       print(exc.code, exc.message)

Rate limits are handled for you: HTTP 429 (and 503 for ``GET``) is retried up
to ``max_retries`` times (default 3), honouring ``Retry-After``. If the server
asks to wait longer than ``max_retry_wait`` seconds (default 60), a
``RateLimitError`` with ``retry_after`` is raised instead of sleeping.

Paging and files
~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path

   # Process a large JQL result without loading it all into memory
   for issue in jira.iter_issues("project = TEST", fields=["summary"]):
       print(issue["key"])

   print(jira.count_issues("project = TEST AND status = Open"))

   jira.update_issue("TEST-1", fields={jira.get_field_id("Story Points"): 3})
   jira.add_attachment("TEST-1", "report.csv", Path("report.csv").read_bytes())

   # Publish a generated report: created the first time, updated afterwards
   confluence.create_or_update_page("SPACE", "Nightly report", "<p>All green</p>")
   confluence.download_attachment(123456, "diagram.png", path="diagram.png")

More Jira, Bitbucket, and Confluence examples are available in the
`documentation <https://atlassian-api-py.readthedocs.io/>`_.

.. start-license

License
-------

This project is released under the `MIT License <LICENSE>`_.

.. end-license

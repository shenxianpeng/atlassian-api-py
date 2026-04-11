Usage Guide
===========

This guide shows the usual path from a new script to common Jira, Bitbucket,
and Confluence operations.

Before You Start
----------------

You need three pieces of information:

* The base URL for your Atlassian product, for example
  ``https://jira.company.com``.
* Credentials supported by that product: username/password or a bearer token.
* Product-specific identifiers such as Jira issue keys, Bitbucket project keys,
  repository slugs, Confluence space keys, or Confluence page IDs.

The library trims trailing slashes from the base URL. Pass paths and IDs exactly
as they appear in your Atlassian instance.

Authentication
--------------

Create a client for the product you want to call.

Username and password:

.. code-block:: python

   from atlassian import Jira

   jira = Jira(
       url="https://jira.company.com",
       username="your_username",
       password="your_password",
   )

Bearer token:

.. code-block:: python

   from atlassian import Jira

   jira = Jira(url="https://jira.company.com", token="your_token")

Configuration file:

.. code-block:: ini

   [jira]
   url = https://jira.company.com
   username = your_username
   password = your_password
   # Or use token instead of username/password:
   token = your_token

.. code-block:: python

   import configparser

   from atlassian import Jira

   config = configparser.ConfigParser()
   config.read("config.ini")
   section = config["jira"]

   jira = Jira(
       url=section["url"],
       username=section.get("username"),
       password=section.get("password"),
       token=section.get("token"),
   )

Keep local configuration files out of version control when they contain
credentials.

Working With Responses
----------------------

``GET`` calls parse JSON into nested ``SimpleNamespace`` objects:

.. code-block:: python

   issue = jira.issue("TEST-1")
   print(issue.key)
   print(issue.fields.summary)
   print(issue.fields.status.name)

When a ``GET`` response body is not JSON, the raw response text is returned.
When the response body is empty, ``None`` is returned.

``POST``, ``PUT``, and ``DELETE`` calls return decoded JSON dictionaries when
the response contains JSON. Empty responses return ``None``.

HTTP ``4xx`` and ``5xx`` responses raise ``APIError``:

.. code-block:: python

   from atlassian.error import APIError

   try:
       issue = jira.issue("MISSING-1")
   except APIError as exc:
       print(f"{exc.code}: {exc.message}")

Clients also work as context managers when you want the underlying
``requests.Session`` to close automatically:

.. code-block:: python

   from atlassian import Jira

   with Jira(url="https://jira.company.com", token="your_token") as jira:
       issue = jira.issue("TEST-1")
       print(issue.fields.summary)

Jira
----

Read an issue:

.. code-block:: python

   from atlassian import Jira

   jira = Jira(url="https://jira.company.com", token="your_token")
   issue = jira.issue("TEST-1")

   print(issue.id)                     # e.g. 1684517
   print(issue.key)                    # e.g. "TEST-1"
   print(issue.fields.summary)         # e.g. "Jira REST API example"
   print(issue.fields.issuetype.name)  # e.g. "Bug"

Search with JQL:

.. code-block:: python

   issues = jira.search_issue_with_jql(
       'project = "TEST" AND status != Done ORDER BY updated DESC',
       max_result=100,
   )
   for issue in issues:
       print(issue["key"])

Update fields and comments:

.. code-block:: python

   jira.update_issue_label("TEST-1", add_labels=["automation"])
   jira.update_issue_description("TEST-1", "Updated by automation.")
   jira.add_issue_comment("TEST-1", "Checked by atlassian-api-py.")

Create an issue with a Jira fields payload:

.. code-block:: python

   jira.create_issue(
       fields={
           "project": {"key": "TEST"},
           "summary": "Created from atlassian-api-py",
           "issuetype": {"name": "Task"},
           "description": "This issue was created through the Jira REST API.",
       }
   )

Transition an issue:

.. code-block:: python

   transitions = jira.get_transitions("TEST-1")
   for transition in transitions.transitions:
       print(transition.id, transition.name)

   jira.issue_transition("TEST-1", transition_id="31")

Bitbucket
---------

Create a Bitbucket client:

.. code-block:: python

   from atlassian import Bitbucket

   bitbucket = Bitbucket(
       url="https://bitbucket.company.com",
       username="your_username",
       password="your_password",
   )

List repositories in a project:

.. code-block:: python

   repos = bitbucket.get_project_repo("PROJECT_KEY")
   for repo in repos:
       print(repo.name)

Read branches and commits:

.. code-block:: python

   branches = bitbucket.get_repo_branch("PROJECT_KEY", "repo_slug")
   commits = bitbucket.get_branch_commits("PROJECT_KEY", "repo_slug", "main")

   print(branches[0].displayId)
   print(commits[0].displayId)

Create and review pull requests:

.. code-block:: python

   bitbucket.create_pull_request(
       project_key="PROJECT_KEY",
       repo_slug="repo_slug",
       title="Add automation update",
       from_branch="feature/automation",
       to_branch="main",
       description="Created from atlassian-api-py.",
       reviewers=["reviewer_slug"],
   )

   overview = bitbucket.get_pull_request_overview("PROJECT_KEY", "repo_slug", 123)
   bitbucket.review_pull_request(
       "PROJECT_KEY",
       "repo_slug",
       pr_id=123,
       user_slug="your_user_slug",
       status="APPROVED",
   )

   # Merge and decline operations require the current pull request version.
   bitbucket.merge_pull_request("PROJECT_KEY", "repo_slug", 123, overview.version)

Confluence
----------

Create a Confluence client:

.. code-block:: python

   from atlassian import Confluence

   confluence = Confluence(
       url="https://confluence.company.com",
       username="your_username",
       password="your_password",
   )

Read pages and spaces:

.. code-block:: python

   page = confluence.get_content_by_id(123456)
   print(page.title)

   spaces = confluence.get_spaces(limit=10)
   for space in spaces.results:
       print(space.key, space.name)

Search with Confluence Query Language:

.. code-block:: python

   results = confluence.search_content('space = "SPACE" AND type = page')
   for result in results.results:
       print(result.title)

Create a page:

.. code-block:: python

   confluence.create_content(
       title="Automation Notes",
       space_key="SPACE",
       body_value="<p>Created from atlassian-api-py.</p>",
   )

Add and remove labels:

.. code-block:: python

   confluence.add_label(123456, "automation")
   confluence.remove_label(123456, "automation")

Low-Level Requests
------------------

Each product client inherits from ``AtlassianAPI``. Use the low-level helpers
when the project does not yet include a convenience method for an endpoint:

.. code-block:: python

   result = jira.get("/rest/api/2/project/TEST")
   jira.post("/rest/api/2/issue/TEST-1/comment", json={"body": "Hello"})

Paths are appended to the base URL exactly as provided.

Troubleshooting
---------------

``401`` or ``403`` errors usually mean the credentials are invalid or the
authenticated user does not have permission for that resource.

``404`` errors usually mean the base URL, project key, repository slug, issue
key, or page ID does not match the target Atlassian instance.

If a value is missing from a response object, inspect the raw Atlassian REST API
response for that endpoint and confirm that the field is included for your
product version and permissions.

For the complete method list, see the class references in :doc:`atlassian`.

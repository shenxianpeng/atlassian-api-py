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

   from atlassian_api import Jira

   jira = Jira(
       url="https://jira.company.com",
       username="your_username",
       password="your_password",
   )

Bearer token:

.. code-block:: python

   from atlassian_api import Jira

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

   from atlassian_api import Jira

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

Atlassian Cloud
---------------

Jira and Confluence clients work against Atlassian Cloud with the same method
calls. Cloud is detected from ``*.atlassian.net`` URLs; pass ``cloud=True`` for
a custom domain, or ``cloud=False`` to force Server/Data Center behaviour.

Authenticate with your account email and an
`API token <https://id.atlassian.com/manage-profile/security/api-tokens>`_ as
``username`` and ``password``. ``token=`` sends a bearer token, which Cloud
accepts only for OAuth 2.0 access tokens.

.. code-block:: python

   from atlassian_api import Jira

   jira = Jira(
       url="https://your-site.atlassian.net",
       username="you@example.com",
       password="your_api_token",
   )

What changes on Cloud:

.. list-table::
   :header-rows: 1

   * - Method
     - Server / Data Center
     - Cloud
   * - ``Jira.search_issue_with_jql()``
     - ``/rest/api/2/search``, ``startAt`` paging
     - ``/rest/api/2/search/jql``, ``nextPageToken`` paging. The JQL must be
       bounded (for example restrict ``project``).
   * - ``Jira.assign_issue()``, ``user()``, ``add_issue_watcher()``
     - username
     - ``accountId``
   * - ``Jira.get_projects()``
     - ``/rest/api/2/project``
     - all pages of ``/rest/api/2/project/search``
   * - ``Jira.issue_changelog()``
     - ``expand=changelog``
     - all pages of ``/rest/api/2/issue/{key}/changelog`` (``expand`` only
       returns recent updates on Cloud), in the same ``changelog.histories``
   * - ``Jira.iter_board_issues()``, ``iter_backlog_issues()``,
       ``iter_sprint_issues()``, ``iter_epic_issues()``
     - ``/rest/agile/1.0/...``, ``startAt`` paging
     - ``/rest/software/1.0/...``, ``nextPageToken`` paging (Cloud
       deprecated the ``/rest/agile/1.0`` issue lists). Boards, sprints and
       epics themselves stay on ``/rest/agile/1.0``.
   * - Confluence pages, spaces, child pages, comments, labels, attachments
     - REST API v1
     - REST API v2 (``/wiki/api/v2``). Lists keep ``results``/``start``/
       ``limit``/``size`` and contain current pages only; items are v2
       objects (a page has ``spaceId``). Pass ``type="blogpost"`` to methods
       that take a content ID when it is a blog post.
   * - ``Confluence.search_content()``
     - REST API v1, ``start`` paging
     - REST API v1, cursor paging (``start``/``limit`` still work)
   * - ``Confluence.add_label()``, ``remove_label()``,
       ``upload_attachment()``
     - REST API v1
     - REST API v1 (still the Cloud endpoint)

Bitbucket support targets Bitbucket Server/Data Center; a ``bitbucket.org``
URL raises ``ValueError``.

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

   from atlassian_api.error import APIError

   try:
       issue = jira.issue("MISSING-1")
   except APIError as exc:
       print(f"{exc.code}: {exc.message}")

Clients also work as context managers when you want the underlying
``requests.Session`` to close automatically:

.. code-block:: python

   from atlassian_api import Jira

   with Jira(url="https://jira.company.com", token="your_token") as jira:
       issue = jira.issue("TEST-1")
       print(issue.fields.summary)

Jira
----

Read an issue:

.. code-block:: python

   from atlassian_api import Jira

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

Boards, Sprints and Epics
~~~~~~~~~~~~~~~~~~~~~~~~~

Jira Software boards, sprints and epics work on Data Center and Cloud with the
same calls.

Sprint report: find the board and its active sprint, then group the sprint's
issues by status.

.. code-block:: python

   from collections import defaultdict

   board = jira.get_boards(project="TEST", board_type="scrum")[0]
   sprint = jira.get_board_sprints(board.id, state="active")[0]

   by_status = defaultdict(list)
   for issue in jira.iter_sprint_issues(sprint.id, fields=["summary", "status"]):
       by_status[issue.fields.status.name].append(issue)

   print(f"{sprint.name}: {sprint.startDate[:10]} to {sprint.endDate[:10]}")
   for status, issues in by_status.items():
       print(f"{status} ({len(issues)})")
       for issue in issues:
           print(f"  {issue.key}  {issue.fields.summary}")

Move issues into a sprint, here the unfinished work of the active sprint into
the next one. Any number of issues can be passed; Jira takes 50 per request,
so they are sent in batches.

.. code-block:: python

   unfinished = [
       issue.key
       for issue in jira.iter_sprint_issues(sprint.id, jql="statusCategory != Done")
   ]
   next_sprint = jira.get_board_sprints(board.id, state="future")[0]
   jira.move_issues_to_sprint(next_sprint.id, unfinished)

   jira.move_issues_to_backlog(["TEST-7", "TEST-8"])  # out of their sprint

Create, start and complete a sprint:

.. code-block:: python

   sprint = jira.create_sprint(
       board.id,
       "Sprint 13",
       start_date="2026-11-16T09:00:00.000+0000",
       end_date="2026-11-27T17:00:00.000+0000",
       goal="Ship the importer",
   )
   jira.update_sprint(sprint["id"], state="active")  # other fields are kept
   jira.update_sprint(sprint["id"], state="closed")

Epics:

.. code-block:: python

   for epic in jira.get_board_epics(board.id, done=False):
       print(epic.id, epic.name)

   for issue in jira.iter_epic_issues("TEST-5", fields=["summary"]):
       print(issue.key, issue.fields.summary)

   jira.move_issues_to_epic("TEST-5", ["TEST-8", "TEST-9"])
   jira.remove_issues_from_epic(["TEST-9"])

Things to know:

* ``get_boards()``, ``get_board_sprints()`` and ``get_board_epics()`` return
  every page as one list; pass ``limit=`` to stop early. The ``iter_*_issues()``
  methods are generators that fetch a page at a time.
* Issues from ``iter_board_issues()``, ``iter_backlog_issues()``,
  ``iter_sprint_issues()`` and ``iter_epic_issues()`` are ``SimpleNamespace``
  objects like the result of ``jira.issue()`` (``issue.fields.status.name``),
  with the Jira Software fields ``sprint``, ``closedSprints``, ``flagged`` and
  ``epic``. ``iter_issues()`` yields dictionaries.
* On Cloud the issue lists come from ``/rest/software/1.0`` and are paged with
  ``nextPageToken``; Cloud deprecated the ``/rest/agile/1.0`` issue lists. The
  response has no ``total`` there.
* The move methods send 50 issues per request. If a request fails, the issues
  of the earlier requests have already been moved.
* ``update_sprint()`` is a partial update: fields you do not pass keep their
  value. A closed sprint cannot be changed on Data Center; on Cloud only its
  name and goal can. Data Center refuses to delete an active or completed
  sprint.
* A board without sprints (a kanban board) answers ``get_board_sprints()``
  with HTTP 400.
* Cloud, team-managed projects: ``get_epic()``, ``iter_epic_issues()``,
  ``move_issues_to_epic()`` and ``remove_issues_from_epic()`` do not work for
  their epics. Use the parent field instead:
  ``jira.iter_issues("parent = TEST-5")`` and
  ``jira.update_issue("TEST-8", fields={"parent": {"key": "TEST-5"}})``.

Bitbucket
---------

Create a Bitbucket client:

.. code-block:: python

   from atlassian_api import Bitbucket

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

   from atlassian_api import Confluence

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

Every error is an ``APIError`` subclass from ``atlassian_api.error``:
``AuthenticationError`` (401), ``PermissionDeniedError`` (403),
``NotFoundError`` (404), ``ConflictError`` (409), ``RateLimitError`` (429, with
``retry_after``) and ``ServerError`` (5xx).

``401`` or ``403`` errors usually mean the credentials are invalid or the
authenticated user does not have permission for that resource. On Cloud, a
``401`` with ``token=`` usually means an API token was sent as a bearer token;
pass it as ``password`` with your email as ``username``.

An ``APIError`` saying an HTML page was received means the server answered with
a web page instead of the REST API, usually a login or SSO redirect. Check the
base URL and the credentials.

Requests rejected with ``429 Too Many Requests`` are retried automatically.
Tune this with ``max_retries`` (``0`` disables it) and ``max_retry_wait``:

.. code-block:: python

   jira = Jira(url=..., username=..., password=..., max_retries=5, max_retry_wait=30)

``404`` errors usually mean the base URL, project key, repository slug, issue
key, or page ID does not match the target Atlassian instance.

If a value is missing from a response object, inspect the raw Atlassian REST API
response for that endpoint and confirm that the field is included for your
product version and permissions.

For the complete method list, see the class references in :doc:`atlassian`.

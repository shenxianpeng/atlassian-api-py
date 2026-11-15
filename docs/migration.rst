Coming from atlassian-python-api
================================

This page is for people who already have scripts written against
`atlassian-python-api <https://github.com/atlassian-api/atlassian-python-api>`_
(import package ``atlassian``) and want to try ``atlassian-api-py`` (import
package ``atlassian_api``). It covers installing both in one environment, what
changes when you port a script, and what you would lose.

.. note::

   Everything said here about ``atlassian-python-api`` was checked against
   version 5.0.5, and about ``atlassian-api-py`` against version 2.0. The
   method names in the tables were verified by introspecting both packages.
   Both libraries keep changing: if something no longer matches, please
   `open an issue <https://github.com/shenxianpeng/atlassian-api-py/issues>`_.

Should you switch?
------------------

``atlassian-python-api`` is the larger library. It covers more Atlassian
products and many more endpoints than ``atlassian-api-py``, which is a small
client for the common Jira, Confluence, and Bitbucket Server/Data Center
operations. Porting is worth it only if what you gain matters to you and what
you lose does not.

``atlassian-api-py`` fits when:

* Your scripts use the operations listed in the `method mapping`_ tables
  below, and little else.
* The same script has to run against Data Center and Cloud. The Jira and
  Confluence clients detect Cloud from the URL and keep their method names and
  arguments on both (see `Cloud and Data Center`_).
* You want one exception class per failure type, retries on HTTP 429 without
  configuration, and an error instead of an HTML login page when an SSO
  redirect gets in the way (see `behaviour differences`_).
* You want few dependencies: ``requests`` is the only one.
  ``atlassian-python-api`` also installs ``oauthlib``, ``requests-oauthlib``,
  ``deprecated``, ``jmespath``, ``beautifulsoup4`` and ``typing-extensions``.

Stay with ``atlassian-python-api`` when:

* You need anything in `What atlassian-api-py does not have`_: Jira Software
  boards, sprints and epics, Jira Service Management, filters, Bitbucket Cloud,
  Bamboo, Crowd, Xray, Assets/Insight and more.
* You authenticate with OAuth 1.0a, Kerberos or cookies and want the client to
  set that up for you.
* You run Python 3.9. ``atlassian-api-py`` needs Python 3.10 or newer.
* Your code base depends on dictionary results in many places and there is no
  reason to touch it.

Using both is a supported option. The two packages install side by side, so
you can keep existing code on ``atlassian-python-api`` and use
``atlassian-api-py`` for new scripts, or only where its Cloud handling or
error classes help.

Installing both side by side
----------------------------

.. code-block:: bash

   pip install atlassian-python-api "atlassian-api-py>=2.0"

Version 2.0 or newer of ``atlassian-api-py`` is required. Earlier releases
used the import name ``atlassian`` too, so the two packages overwrote each
other's files.

Both can then be imported in one script:

.. code-block:: python

   from atlassian import Jira as PythonApiJira  # atlassian-python-api
   from atlassian_api import Jira  # atlassian-api-py

   URL = "https://jira.example.com"

   legacy = PythonApiJira(url=URL, username="user", password="secret")
   jira = Jira(url=URL, username="user", password="secret")

   print(type(legacy).__module__)  # atlassian.jira.jira_server
   print(type(jira).__module__)  # atlassian_api.jira

Upgrading atlassian-api-py from 1.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``atlassian-api-py`` 1.x is already installed next to
``atlassian-python-api``, reinstall ``atlassian-python-api`` after upgrading.
Uninstalling 1.x removes the ``atlassian`` files the two packages shared, and
imports from ``atlassian`` fail until they are restored:

.. code-block:: bash

   pip install --upgrade atlassian-api-py
   pip install --force-reinstall --no-deps atlassian-python-api

Then change ``from atlassian import ...`` to ``from atlassian_api import ...``
in the scripts that used ``atlassian-api-py`` 1.x. The :doc:`changelog` lists
the other changes in 2.0.

Creating clients
----------------

The constructors take the same ``url``, ``username``, ``password`` and
``token`` arguments, so the simplest clients only need a different import:

.. code-block:: python

   # atlassian-python-api
   from atlassian import Jira

   jira = Jira(url="https://jira.example.com", token="personal-access-token")

   # atlassian-api-py
   from atlassian_api import Jira

   jira = Jira(url="https://jira.example.com", token="personal-access-token")

On Atlassian Cloud both use the account email as ``username`` and an API token
as ``password``. ``atlassian.Jira`` has to be told that the site is Cloud;
``atlassian_api.Jira`` reads it from the URL:

.. code-block:: python

   # atlassian-python-api
   from atlassian import Jira

   jira = Jira(
       url="https://example.atlassian.net",
       username="you@example.com",
       password="api-token",
       cloud=True,
   )

   # atlassian-api-py
   from atlassian_api import Jira

   jira = Jira(
       url="https://example.atlassian.net",
       username="you@example.com",
       password="api-token",
   )

Options for TLS, proxies and timeouts have different names or defaults:

.. code-block:: python

   # atlassian-python-api
   from atlassian import Confluence

   confluence = Confluence(
       url="https://confluence.example.com",
       username="user",
       password="secret",
       verify_ssl=False,
       proxies={"https": "http://proxy.example.com:8080"},
       timeout=30,
   )

   # atlassian-api-py
   from atlassian_api import Confluence

   confluence = Confluence(
       url="https://confluence.example.com",
       username="user",
       password="secret",
       verify=False,
       proxies={"https": "http://proxy.example.com:8080"},
       timeout=30,
   )

.. list-table:: Constructor arguments
   :header-rows: 1
   :widths: 20 40 40

   * - Topic
     - atlassian-python-api
     - atlassian-api-py
   * - Basic auth, bearer token
     - ``username`` and ``password``, or ``token``
     - The same names. ``token`` sends ``Authorization: Bearer`` in both.
   * - Cloud
     - ``cloud`` defaults to ``False`` in ``Jira`` and the URL is not
       inspected, so pass ``cloud=True``. ``Confluence`` detects Cloud from
       the URL.
     - Detected from the URL (``*.atlassian.net``, ``*.jira.com``,
       ``api.atlassian.com``). Pass ``cloud=True`` for a custom domain or
       ``cloud=False`` to force Server/Data Center behaviour.
   * - TLS verification
     - ``verify_ssl``
     - ``verify``: ``True``, ``False``, or the path of a CA bundle
   * - Client certificate
     - ``cert``
     - No argument. Set ``cert`` on a ``requests.Session`` and pass it as
       ``session``.
   * - Proxies
     - ``proxies``
     - ``proxies``
   * - Timeout
     - ``timeout``, 75 seconds by default
     - ``timeout``, 60 seconds by default
   * - Existing session
     - ``session``. The value of ``session.verify`` is kept.
     - ``session``. The client sets ``session.verify`` from its ``verify``
       argument (``True`` by default), so repeat a custom CA bundle as
       ``verify``.
   * - OAuth 1.0a, OAuth 2.0, Kerberos, cookies, custom header
     - ``oauth``, ``oauth2``, ``kerberos``, ``cookies``, ``header``
     - No arguments. Pass an OAuth 2.0 access token as ``token``, or configure
       a ``requests.Session`` yourself and pass it as ``session``.
   * - API root and version
     - ``api_root``, ``api_version``
     - No arguments. Each helper calls a fixed path.
   * - Raw ``requests.Response``
     - ``advanced_mode=True``
     - No flag. ``client.request()`` returns the response.
   * - Retries
     - ``backoff_and_retry``, ``retry_status_codes``, ``max_backoff_seconds``,
       ``max_backoff_retries``, ``retry_with_header``
     - ``max_retries``, ``max_retry_wait`` (see `Retries and rate limits`_)

Pass constructor arguments by keyword. After ``url``, ``username``,
``password`` and ``timeout`` the positional order differs between the two
libraries. Both clients work as context managers and close their session on
exit.

Method mapping
--------------

The tables list the commonly used operations that both libraries have. The
left column is the ``atlassian-python-api`` method, the middle column the
``atlassian-api-py`` method that replaces it. Three things apply to every row:

* Read methods return dictionaries on the left and attribute objects on the
  right (see `Return values`_).
* ``atlassian-api-py`` helpers have fewer optional arguments. Where a row says
  an argument is missing, call the endpoint with the low-level helpers
  described in `Endpoints without a helper`_.
* Keyword arguments are often named differently, for example
  ``repository_slug`` and ``pull_request_id`` on the left are ``repo_slug``
  and ``pr_id`` on the right. Check the signature in :doc:`atlassian` when
  you pass arguments by keyword.

Jira
~~~~

The left column is ``atlassian.Jira``, which in 5.0.5 is the Server/Data
Center client ``atlassian.jira.jira_server.Jira``. It also talks to Cloud when
created with ``cloud=True``. ``atlassian.JiraCloud`` is a separate client for
the Cloud REST API v2/v3 with a different set of methods; it is not covered
here.

.. list-table:: Jira methods
   :header-rows: 1
   :widths: 28 28 44
   :name: jira-methods

   * - atlassian-python-api
     - atlassian-api-py
     - Notes
   * - ``issue()``, ``get_issue()``
     - ``issue()``
     - Takes the issue key only; there is no ``fields`` or ``expand``
       argument.
   * - ``create_issue()``, ``issue_create()``
     - ``create_issue()``
     - Same ``fields`` payload, and the same optional ``update`` payload as
       the left ``create_issue()``.
   * - ``update_issue_field()``
     - ``update_issue()``
     - Pass the dictionary as ``fields``.
   * - ``issue_update()``
     - ``update_issue()``
     - ``fields``, ``update`` and ``notify_users`` carry over. There is no
       ``history_metadata`` or ``properties`` argument.
   * - ``edit_issue()``
     - ``update_issue()``
     - The left method sends its ``fields`` argument as Jira's ``update``
       operations, so pass that dictionary as ``update``.
   * - ``update_issue()``
     - ``update_issue()``
     - Same name, different arguments. The left method takes the whole
       request body; the right one takes ``fields`` and ``update``
       separately.
   * - ``assign_issue()``
     - ``assign_issue()``
     - The second argument is ``account_id`` on the left and ``assignee`` on
       the right. Both send a username on Server/Data Center and an
       ``accountId`` on Cloud.
   * - ``get_issue_transitions()``
     - ``get_transitions()``
     - The left method returns a list of ``name``/``id``/``to`` dictionaries.
       The right one returns Jira's response: read ``.transitions`` and each
       item's ``.id``, ``.name`` and ``.to.name``.
   * - ``set_issue_status()``, ``issue_transition()``
     - ``issue_transition()``
     - Mind the name: ``issue_transition()`` exists on both sides. The left
       methods take the name of the target status and look up the
       transition. The right method takes a transition ID; find it with
       ``get_transitions()``. It cannot set ``fields`` or ``update`` during
       the transition.
   * - ``issue_add_comment()``
     - ``add_issue_comment()``
     - No ``visibility`` argument.
   * - ``issue_edit_comment()``
     - ``update_issue_comment()``
     - No ``visibility`` or ``notify_users`` argument.
   * - ``issue_get_comments()``
     - ``get_issue_comments()``
     -
   * - ``jql()``
     - ``search_issue_with_jql()``
     - The left method returns one page of results as Jira sends it
       (``issues``, ``total``). The right one fetches every page and returns
       the list of issues; ``max_result`` is the page size. Without
       ``fields`` the left asks for ``*all`` and the right gets Jira's
       navigable fields.
   * - ``jql_get_list_of_tickets()``
     - ``search_issue_with_jql()``, ``iter_issues()``
     - Both sides fetch every page. ``iter_issues()`` yields issues while it
       pages instead of building a list.
   * - ``enhanced_jql()``, ``enhanced_jql_get_list_of_tickets()``
     - ``search_issue_with_jql()``, ``iter_issues()``
     - The left methods are for Cloud only. The right methods choose the
       endpoint themselves.
   * - ``approximate_issue_count()``
     - ``count_issues()``
     - The left method is for Cloud only and returns Jira's response. The
       right one returns an ``int`` on Cloud and Server/Data Center.
   * - ``add_attachment()``
     - ``add_attachment()``
     - Same name, different arguments. The left method opens the file at
       ``filename``. The right one takes a ``filename`` for the attachment
       and its contents as ``file_data`` bytes.
   * - ``add_attachment_object()``
     - ``add_attachment()``
     - Pass the bytes read from the file object.
   * - ``get_attachment()``
     - ``get_attachment()``
     - Attachment metadata.
   * - ``get_attachment_content()``
     - ``download_attachment()``
     - Returns bytes, or streams to a file when ``path`` is given.
   * - ``remove_attachment()``
     - ``delete_attachment()``
     -
   * - ``issue_worklog()``
     - ``add_worklog()``
     - The left method takes ``started`` and the duration in seconds as
       ``time_sec``. The right one takes a Jira duration string such as
       ``"1h 30m"`` as ``time_spent``; ``started`` is optional.
   * - ``issue_get_worklog()``
     - ``get_worklogs()``
     - The left library's own ``get_worklogs()`` is a different call: it
       fetches worklogs by a list of worklog IDs.
   * - ``issue_add_watcher()``
     - ``add_issue_watcher()``
     -
   * - ``issue_get_watchers()``
     - ``get_issue_watchers()``
     -
   * - ``user()``
     - ``user()``
     - The left method has ``username``, ``key`` and ``account_id``
       arguments. The right one takes one value: the username on Server/Data
       Center, the ``accountId`` on Cloud.
   * - ``user_find_by_user_string()``
     - ``search_users()``
     - One ``query`` argument on both deployments.
   * - ``projects()``, ``get_all_projects()``
     - ``get_projects()``
     -
   * - ``project()``, ``get_project()``
     - ``get_project()``
     - No ``expand`` argument.
   * - ``get_project_components()``
     - ``get_project_components()``
     -
   * - ``get_project_versions()``
     - ``get_versions()``
     -
   * - ``add_version()``
     - ``create_version()``
     - Takes the project key and the version ``name``. On Cloud it looks up
       the numeric project ID that Jira needs.
   * - ``get_all_fields()``
     - ``get_fields()``
     - ``get_field_id()`` returns a field's ID from its display name.
   * - ``get_issue_changelog()``
     - ``issue_changelog()``
     - The right method returns the issue with its changelog in
       ``.changelog.histories`` (every page of it on Cloud); it has no
       ``start`` or ``limit`` argument.
   * - ``create_issue_link()``
     - ``link_issue_as()``
     - The left method takes the request body. The right one takes
       ``type_name``, ``inward_issue`` and ``outward_issue``.
   * - ``remove_issue_link()``
     - ``delete_issue_link()``
     -
   * - ``delete_issue()``
     - ``delete_issue()``
     - The left method asks Jira to delete sub-tasks too
       (``delete_subtasks=True`` by default). The right one does not send
       that parameter.

Confluence
~~~~~~~~~~

In 5.0.5 ``atlassian.Confluence`` is a thin wrapper that picks an
implementation from the URL and forwards method calls to it. The left column
lists the methods of its Server/Data Center implementation, which is also
exported as ``atlassian.ConfluenceServer``. For an ``*.atlassian.net`` URL the
wrapper uses a separate Cloud implementation with a different set of methods:
``get_page_by_id()``, ``create_page()`` and ``update_page()``, for example,
are not available on it. The ``atlassian-api-py`` methods in the middle column
work on both deployments.

.. list-table:: Confluence methods
   :header-rows: 1
   :widths: 28 28 44
   :name: confluence-methods

   * - atlassian-python-api
     - atlassian-api-py
     - Notes
   * - ``get_page_by_id()``
     - ``get_content_by_id()``
     - No ``expand`` argument. On Cloud the body is included in storage
       format. To request the body or other expansions on Server/Data
       Center, call the endpoint with the low-level ``get()``.
   * - ``get_page_by_title()``
     - ``get_page_by_title()``
     - Both return Confluence's list response; the page, if any, is the first
       item of ``results``.
   * - ``get_page_id()``
     - ``get_page_by_title()``
     - Read ``.results[0].id``.
   * - ``create_page()``
     - ``create_content()``
     - The argument order differs: ``title``, ``space_key``, ``body_value``,
       then ``ancestors_id`` for the parent. The body is always storage
       format.
   * - ``update_page()``
     - ``update_content()``
     - The right method always sends the update; the left one skips it when
       the body is unchanged unless ``always_update`` is set. There is no
       ``parent_id``, ``minor_edit`` or ``version_comment`` argument.
   * - ``update_or_create()``
     - ``create_or_update_page()``
     - The argument order differs: ``space_key``, ``title``, ``body_value``,
       then ``parent_id``. An existing page is found by title in the space
       and is not moved.
   * - ``remove_page()``, ``remove_content()``
     - ``delete_content()``
     - No ``recursive`` argument.
   * - ``get_page_child_by_type()``, ``get_child_pages()``
     - ``get_child_pages()``
     - The right method returns one page of results (25 by default) with
       ``start`` and ``limit`` arguments. Called without ``start`` and
       ``limit``, the left ``get_page_child_by_type()`` iterates over all
       children.
   * - ``get_page_labels()``
     - ``get_labels()``
     -
   * - ``set_page_label()``
     - ``add_label()``
     -
   * - ``remove_page_label()``
     - ``remove_label()``
     -
   * - ``attach_file()``, ``attach_content()``
     - ``upload_attachment()``
     - Takes the page ID, a ``filename`` and the contents as ``file_data``
       bytes. It always creates a new attachment; the left methods update an
       existing attachment of the same name. The page cannot be given by
       ``title`` and ``space``.
   * - ``get_attachments_from_content()``
     - ``get_attachments()``
     - No ``start``, ``limit`` or ``filename`` argument.
   * - ``download_attachments_from_page()``
     - ``download_attachment()``
     - Downloads one attachment, named by ``filename``. Returns bytes, or
       streams to a file when ``path`` is given.
   * - ``cql()``
     - ``search_content()``
     - Different endpoints on Server/Data Center: the left method calls
       ``/rest/api/search``, whose results wrap each content object in a
       ``content`` key; the right one calls ``/rest/api/content/search``,
       whose results are the content objects.
   * - ``iter_cql()``, ``cql_all()``
     - ``iter_search()``
     - Yields every result. The endpoint difference of ``cql()`` applies.
   * - ``get_all_spaces()``
     - ``get_spaces()``
     - ``limit`` defaults to 50 on the left and 25 on the right.
   * - ``get_space()``
     - ``get_space()``
     - No ``expand`` argument.
   * - ``get_all_pages_from_space_raw()``
     - ``get_content_by_space()``
     - One page of results. To walk a whole space, as the left
       ``get_all_pages_from_space()`` does, use ``iter_search()`` with a CQL
       query on the space.
   * - ``get_page_comments()``
     - ``get_comments()``
     -
   * - ``add_comment()``
     - ``add_comment()``
     -
   * - ``history()``, ``get_content_history()``
     - ``get_content_history()``
     - On Cloud the right method returns the list of versions.
   * - ``get_page_as_pdf()``, ``export_page()``
     - ``export_page_pdf()``
     - Server/Data Center only on the right; on Cloud it raises
       ``NotImplementedError``. Returns bytes, or writes to ``path``.

Bitbucket Server/Data Center
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The left column is ``atlassian.Bitbucket`` used against Bitbucket Server/Data
Center. ``atlassian-api-py`` has no Bitbucket Cloud support: its ``Bitbucket``
class raises ``ValueError`` for a ``bitbucket.org`` URL.

.. list-table:: Bitbucket methods
   :header-rows: 1
   :widths: 28 28 44
   :name: bitbucket-methods

   * - atlassian-python-api
     - atlassian-api-py
     - Notes
   * - ``repo_list()``
     - ``get_project_repo()``
     - ``get_project_repo_name()`` returns only the names.
   * - ``get_repo()``
     - ``get_repo_info()``
     -
   * - ``get_branches()``
     - ``get_repo_branch()``
     - No ``filter``, ``base`` or ``order_by`` argument.
   * - ``create_branch()``
     - ``create_branch()``
     - No ``message`` argument.
   * - ``delete_branch()``
     - ``delete_branch()``
     - ``end_point`` (the branch's current commit) is required on the right.
   * - ``get_default_branch()``
     - ``get_default_branch()``
     -
   * - ``get_pull_requests()``
     - ``get_pull_request()``
     - Mind the name: on the right, ``get_pull_request()`` lists pull
       requests. The state argument is ``pr_state`` and defaults to ``ALL``;
       the left default is ``OPEN``.
   * - ``get_pull_request()``
     - ``get_pull_request_overview()``
     - One pull request by ID.
   * - ``open_pull_request()``
     - ``create_pull_request()``
     - The right method creates a pull request between two branches of one
       repository: ``from_branch`` and ``to_branch`` are branch names without
       ``refs/heads/``. ``reviewers`` is a list of user slugs.
   * - ``create_pull_request()``
     - ``create_pull_request()``
     - Same name, different arguments. The left method takes the request
       body as ``data``.
   * - ``merge_pull_request()``
     - ``merge_pull_request()``
     - Same name, different arguments. The fourth argument is
       ``merge_message`` on the left and ``pr_version`` on the right, which
       has no merge message or strategy argument.
   * - ``decline_pull_request()``
     - ``decline_pull_request()``
     -
   * - ``get_pull_requests_activities()``
     - ``get_pull_request_activities()``
     -
   * - ``get_pull_requests_commits()``
     - ``get_pull_request_commits()``
     - The right method returns Bitbucket's first page of commits, in
       ``.values``.
   * - ``add_pull_request_comment()``
     - ``add_pull_request_comment()``
     - No ``parent_id`` argument for replies.
   * - ``update_pull_request_comment()``
     - ``update_pull_request_comment()``
     - Same name, different arguments. The left method takes the comment ID
       and version. The right one finds the comment by its text
       (``old_comment``) and replaces it with ``new_comment``.
   * - ``delete_pull_request_comment()``
     - ``delete_pull_request_comment()``
     - Same name, different arguments. The right method finds the comment by
       its exact text.
   * - ``change_reviewed_status()``
     - ``review_pull_request()``
     - The last two arguments are swapped: ``user_slug``, then ``status``.
   * - ``update_pull_request()``
     - ``update_pull_request_title()``, ``update_pull_request_description()``,
       ``update_pull_request_reviewers()``,
       ``update_pull_request_destination()``
     - The left method takes the request body. The right methods change one
       property each and read the current pull request version themselves.
   * - ``get_commits()``
     - ``get_branch_commits()``, ``get_file_change_history()``
     - ``get_branch_commits()`` lists the commits reachable from a branch;
       ``get_file_change_history()`` lists those that touched one file. There
       is no ``since`` or ``merges`` argument.
   * - ``get_changelog()``
     - ``compare_commits()``
     - ``compare_changes()`` lists the changed files for the same two refs.
   * - ``get_content_of_file()``
     - ``get_file_content()``
     - The argument order differs: the branch comes before the file path.
       The left method returns bytes. The right one returns text, or a parsed
       object when the file contains JSON.
   * - ``get_file_list()``
     - ``list_files()``
     - The directory is ``sub_folder`` on the left and ``path`` on the
       right; the ref is ``query`` on the left and ``at`` on the right.
   * - ``get_tags()``
     - ``get_tags()``
     - No ``filter`` or ``order_by`` argument.
   * - ``set_tag()``
     - ``create_tag()``
     -
   * - ``repo_users()``, ``repo_groups()``
     - ``get_repo_permissions()``
     - Choose with ``principal``: ``"users"`` (the default) or ``"groups"``.
   * - ``repo_grant_user_permissions()``, ``repo_grant_group_permissions()``
     - ``set_repo_permission()``
     - Choose with ``principal``.
   * - ``repo_remove_user_permissions()``,
       ``repo_remove_group_permissions()``
     - ``revoke_repo_permission()``
     - Choose with ``principal``.
   * - ``get_webhooks()``
     - ``get_webhooks()``
     - No ``event`` or ``statistics`` argument.
   * - ``create_webhook()``
     - ``create_webhook()``
     - The positional order differs: the right method takes ``url`` before
       ``events``, and ``active`` defaults to ``True``. There is no
       ``secret`` argument.
   * - ``delete_webhook()``
     - ``delete_webhook()``
     -
   * - ``get_associated_build_statuses()``
     - ``get_build_status()``
     -

Endpoints without a helper
~~~~~~~~~~~~~~~~~~~~~~~~~~

Every client has ``get()``, ``post()``, ``put()``, ``delete()`` and
``request()`` for endpoints and parameters that have no helper. They use the
client's session, error classes and retries:

.. code-block:: python

   from atlassian_api import Jira

   jira = Jira(url="https://jira.example.com", token="personal-access-token")

   issue = jira.get(
       "/rest/api/2/issue/TEST-1",
       params={"fields": "summary,status", "expand": "renderedFields"},
   )
   jira.post("/rest/api/2/issue/TEST-1/comment", json={"body": "Hello"})

The paths are the REST paths below the base URL, as in Atlassian's API
documentation. ``atlassian-python-api`` has helpers of the same names, with
two differences: its ``get()`` returns dictionaries, and its ``post()`` and
``put()`` serialise the ``data`` argument to JSON, where ``atlassian-api-py``
expects the payload as ``json``.

Behaviour differences
---------------------

These are the differences that change how a ported script behaves, beyond
method names.

Return values
~~~~~~~~~~~~~

``atlassian-python-api`` returns the decoded JSON: dictionaries and lists.
``atlassian-api-py`` returns nested ``types.SimpleNamespace`` objects from
``GET`` helpers, so fields are attributes:

.. code-block:: python

   # atlassian-python-api
   issue = jira.issue("TEST-1")
   print(issue["fields"]["status"]["name"])

   # atlassian-api-py
   issue = jira.issue("TEST-1")
   print(issue.fields.status.name)

* A field that is absent raises ``AttributeError`` instead of ``KeyError``.
  Use ``getattr(obj, "name", None)`` where you used ``.get("name")``.
* Keys that are not valid Python names, such as the
  ``com.atlassian...:...`` keys in Bitbucket branch metadata, are read with
  ``getattr()`` or through ``vars(obj)``.
* Helpers that write (``POST``, ``PUT``, ``DELETE``) return the decoded JSON
  dictionary, or ``None`` for an empty response, as in
  ``atlassian-python-api``.
* ``Jira.search_issue_with_jql()`` and ``Jira.iter_issues()`` send ``POST``
  requests, so they return issues as dictionaries: ``issue["key"]``.
* Bitbucket helpers that list things return a Python ``list`` of namespace
  objects.
* Download helpers return ``bytes``, or the ``pathlib.Path`` they wrote.

Errors
~~~~~~

.. code-block:: python

   # atlassian-python-api
   from requests import HTTPError

   try:
       jira.issue("MISSING-1")
   except HTTPError as exc:
       if exc.response.status_code == 404:
           print("no such issue")
       else:
           raise

   # atlassian-api-py
   from atlassian_api.error import APIError, NotFoundError

   try:
       jira.issue("MISSING-1")
   except NotFoundError:
       print("no such issue")
   except APIError as exc:
       print(exc.code, exc.message)
       raise

* ``atlassian-python-api`` raises ``requests.HTTPError`` for HTTP ``4xx`` and
  ``5xx`` responses, with a message built from Atlassian's error JSON. Some
  methods, mostly in the Confluence client, turn particular status codes into
  ``atlassian.errors.ApiError`` subclasses such as ``ApiNotFoundError`` and
  ``ApiPermissionError``.
* ``atlassian-api-py`` always raises ``atlassian_api.error.APIError`` or one
  of its subclasses: ``AuthenticationError`` (401), ``PermissionDeniedError``
  (403), ``NotFoundError`` (404), ``ConflictError`` (409), ``RateLimitError``
  (429) and ``ServerError`` (5xx). ``exc.code`` is the status code and
  ``exc.message`` the response body.
* ``APIError`` is not a ``requests`` exception. An existing
  ``except HTTPError`` or ``except RequestException`` block will not catch it.
  Connection failures and timeouts are still ``requests`` exceptions in both
  libraries.
* When the server answers ``200`` with an HTML page where JSON was expected,
  typically an SSO or login redirect, ``atlassian-api-py`` raises
  ``APIError``. The ``get()`` of ``atlassian-python-api`` returns the page as
  a string in that case.
* ``atlassian-api-py`` refuses to send a request to an absolute URL on
  another host than the client's (``ValueError``), so credentials are not
  sent elsewhere.

Pagination
~~~~~~~~~~

* **Jira search.** ``Jira.search_issue_with_jql()`` returns all matching
  issues as one list, and ``Jira.iter_issues()`` yields them page by page.
  There is no single-page call like ``jql()`` with ``start`` and ``limit``.
* **Confluence lists.** The list methods (``get_spaces()``,
  ``get_content_by_space()``, ``get_child_pages()``, ``search_content()``)
  return one page of results with ``results``, ``start``, ``limit`` and
  ``size``, and take ``start`` and ``limit``. Only ``iter_search()`` walks all
  pages. Several ``atlassian-python-api`` methods return generators over all
  pages instead, for example ``get_all_pages_from_space()``.
* **Bitbucket lists.** ``atlassian-python-api`` returns generators that fetch
  pages as you iterate, and ``limit`` is the page size. ``atlassian-api-py``
  fetches all pages and returns a list, and ``limit`` caps the total number
  of items returned.

Retries and rate limits
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Situation
     - atlassian-python-api (defaults)
     - atlassian-api-py (defaults)
   * - HTTP 429 with ``Retry-After``
     - Waits as asked and retries once
     - Waits as asked and retries up to 3 times
   * - HTTP 429 without ``Retry-After``
     - Not retried
     - Retried up to 3 times, waiting 1, 2, then 4 seconds
   * - HTTP 503
     - Not retried
     - Retried for ``GET`` requests only
   * - ``Retry-After`` longer than the configured maximum
     - Waits ``max_backoff_seconds`` (1800 by default)
     - Raises ``RateLimitError`` at once, with the delay in ``retry_after``,
       when it exceeds ``max_retry_wait`` (60 by default)

``atlassian-python-api`` retries more when created with
``backoff_and_retry=True``: exponential backoff for the status codes in
``retry_status_codes`` (413, 429 and 503 by default). The closest settings in
``atlassian-api-py`` are ``max_retries`` (``0`` turns retries off) and
``max_retry_wait``; the set of retried status codes is fixed.

Cloud and Data Center
~~~~~~~~~~~~~~~~~~~~~

* ``atlassian-api-py`` has one ``Jira`` and one ``Confluence`` class. On
  Cloud they switch endpoints where the two deployments differ and keep the
  method names and arguments. :doc:`usage` lists what changes.
* ``atlassian-python-api`` 5.0.5 has ``Jira`` (Server/Data Center, and Cloud
  with ``cloud=True``) and ``JiraCloud``; ``Confluence`` forwards to a
  Server/Data Center or a Cloud implementation with different method sets,
  and ``ConfluenceV2`` is a client for the Cloud REST API v2.
* Jira Cloud search differs in one detail: ``atlassian.Jira`` calls the REST
  API v3 search endpoint, and ``atlassian_api.Jira`` calls the v2 one. In v3,
  rich-text fields such as ``description`` are Atlassian Document Format
  objects; in v2 they are strings.
* Users are ``accountId`` values on Cloud in both libraries.
* On Confluence Cloud, ``atlassian-api-py`` returns REST API v2 objects: a
  page has ``spaceId`` instead of ``space.key``. Methods that take a content
  ID need ``type="blogpost"`` for blog posts.
* Bitbucket Cloud is supported by ``atlassian-python-api``
  (``atlassian.bitbucket.Cloud``) and not by ``atlassian-api-py``.

Logging
~~~~~~~

Both libraries use the standard ``logging`` module. The logger names differ:
``atlassian.*`` and ``atlassian_api.*``. A level or handler set on
``logging.getLogger("atlassian")`` does not apply to ``atlassian_api``.
``atlassian-api-py`` attaches only a ``NullHandler``, so it prints nothing
unless the application configures logging.

At ``DEBUG`` level ``atlassian-python-api`` logs each request as a ``curl``
command and each response body. ``atlassian-api-py`` logs the method and
status of each request at ``DEBUG`` and each retry at ``WARNING``.

What atlassian-api-py does not have
-----------------------------------

If one of these matters to you, stay with ``atlassian-python-api`` or use both
libraries side by side.

* **Jira:** no Jira Software (Agile) API: boards, sprints, epics and
  backlogs. No Jira Service Management. No filters, dashboards, groups,
  permissions, issue properties or remote links, and no project or user
  administration.
* **Confluence:** no space creation, deletion or permissions, no templates,
  no page restrictions, properties or moves, no user or group management, and
  no export other than a page as PDF on Server/Data Center.
* **Bitbucket:** Server/Data Center only, no Bitbucket Cloud. No project or
  repository creation and deletion, no forks, no branch permissions and no
  Code Insights.
* **Other products:** no Bamboo, Crowd, Xray, Assets/Insight, Tempo,
  Portfolio, Marketplace, Compass or Cloud Admin clients.
* **Authentication:** basic auth and bearer tokens only. OAuth 1.0a,
  Kerberos and cookie authentication need a ``requests.Session`` that you
  configure yourself.
* **Fewer arguments:** most helpers have no ``expand`` and few optional
  arguments, and there is no ``advanced_mode``.
* **No async client.** Both libraries are synchronous and built on
  ``requests``.
* **Python 3.9** is not supported.

The low-level helpers in `Endpoints without a helper`_ reach any REST endpoint
on the same server, including the ones above. They save you from writing the
session and error handling, not the request and response handling that the
helpers of ``atlassian-python-api`` give you.

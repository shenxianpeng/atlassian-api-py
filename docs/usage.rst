
Usage Guide
===========

This guide demonstrates how to connect to Atlassian Jira, Bitbucket, and Confluence using the `atlassian-api-py` library, and how to perform common operations.

Authentication
--------------

You can authenticate using either username/password or a personal access token. Credentials can be provided directly or loaded from a configuration file.

Example: Connect to Jira with username and password

.. code-block:: python

   from atlassian import Jira
   jira = Jira(url="https://jira.company.com", username="your_username", password="your_password")

Example: Connect to Jira with a token

.. code-block:: python

   from atlassian import Jira
   jira = Jira(url="https://jira.company.com", token="your_token")

Example: Load credentials from ``config.ini``

.. code-block:: ini

   [jira]
   url = https://jira.company.com
   username = your_username
   password = your_password
   token = your_token

.. code-block:: python

   import configparser
   config = configparser.ConfigParser()
   config.read("config.ini")
   jira = Jira(
       url=config["jira"]["url"],
       username=config["jira"].get("username"),
       password=config["jira"].get("password"),
       token=config["jira"].get("token"),
   )

Jira Usage
----------

Get issue fields

.. code-block:: python

   issue = jira.issue("TEST-1")
   print(issue.fields.status.name)      # e.g. "Triage"
   print(issue.fields.description)      # e.g. "This is a demo Jira ticket"
   print(issue.fields.issuetype.name)   # e.g. "Bug"

Get additional issue details

.. code-block:: python

   print(issue.id)                     # e.g. 1684517
   print(issue.key)                    # e.g. "TEST-1"
   print(issue.fields.assignee.key)    # e.g. "xpshen"
   print(issue.fields.summary)         # e.g. "Jira REST API Unit Test Example"

Bitbucket Usage
---------------

Get repository information

.. code-block:: python

   from atlassian import Bitbucket
   bitbucket = Bitbucket(url="https://bitbucket.company.com", username="your_username", password="your_password")
   repo_info = bitbucket.get_repo_info("PROJECT_KEY", "repo_slug")
   print(repo_info.name)               # e.g. "My Repository"
   print(repo_info.project.key)        # e.g. "PROJECT_KEY"

List repositories in a project

.. code-block:: python

   repos = bitbucket.get_project_repo("PROJECT_KEY")
   for repo in repos:
       print(repo.name)

Confluence Usage
----------------

Get page information

.. code-block:: python

   from atlassian import Confluence
   confluence = Confluence(url="https://confluence.company.com", username="your_username", password="your_password")
   page = confluence.get_page_by_title("SPACE_KEY", "Page Title")
   print(page.title)                   # e.g. "My Page"
   print(page.body)                    # Page content

For more advanced usage and API details, refer to the full documentation and class references.

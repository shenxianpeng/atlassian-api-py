Python Wrapper for Atlassian REST API
=====================================

.. start-overview

.. |pypi-version| image:: https://img.shields.io/pypi/v/atlassian-api-py
   :target: https://pypi.org/project/atlassian-api-py/
   :alt: PyPI

.. |docs-badge| image:: https://readthedocs.org/projects/atlassian-api-py/badge/?version=latest
   :target: https://atlassian-api-py.readthedocs.io/
   :alt: Documentation

.. |coverage-badge| image:: https://codecov.io/gh/shenxianpeng/atlassian-api-py/graph/badge.svg?token=UE90982FF2
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

A Python wrapper for the Atlassian REST API, supporting JIRA, Bitbucket, and Confluence.

It streamlines integration with Atlassian products.

📘 Documentation: `atlassian-api-py.readthedocs.io <https://atlassian-api-py.readthedocs.io/>`_

.. end-overview

.. start-install

Installation
------------

To install the package, run the following command:

.. code-block:: bash

   $ pip install atlassian-api-py

To upgrade to the latest version, use:

.. code-block:: bash

   $ pip install atlassian-api-py --upgrade

.. end-install

Usage
-----

You can authenticate using either username/password or a personal access token. Credentials can be provided directly or loaded from a configuration file.

Using username and password
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Jira
   jira = Jira(url='https://jira.company.com', username="your_username", password="your_password")

Using a token
~~~~~~~~~~~~~

.. code-block:: python

   from atlassian import Jira
   jira = Jira(url='https://jira.company.com', token="your_token")

Alternatively, load credentials from ``config.ini`` file:

.. code-block:: ini

   [jira]
   url = https://jira.company.com
   username = your_username
   password = your_password
   # Alternatively
   token = your_token

.. code-block:: python

   import configparser
   config = configparser.ConfigParser()
   config.read('config.ini')

   jira_url = config['jira']['url']
   jira_usr = config['jira']['username']
   jira_psw = config['jira']['password']
   # Alternatively
   jira_token = config['jira']['token']

Jira Usage
~~~~~~~~~~

Getting issue fields

.. code-block:: python

   issue = jira.issue("TEST-1")
   print(issue.fields.status.name)      # e.g. "Triage"
   print(issue.fields.description)      # e.g. "This is a demo Jira ticket"
   print(issue.fields.issuetype.name)   # e.g. "Bug"

Get additional issue details

.. code-block:: python

   print(issue.id)                      # e.g. 1684517
   print(issue.key)                     # e.g. "TEST-1"
   print(issue.fields.assignee.key)     # e.g. "xpshen"
   print(issue.fields.summary)          # e.g. "Jira REST API Unit Test Example"

More about Jira, Bitbucket, and Confluence API usage can be found in the `documentation <https://atlassian-api-py.readthedocs.io/>`_

.. start-license

License
-------

This project is released under the `MIT License <LICENSE>`_.

.. end-license

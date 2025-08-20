Python Wrapper for Atlassian REST API
=====================================

.. start-overview

.. |pypi-version| image:: https://img.shields.io/pypi/v/atlassian-api-py
   :target: https://pypi.org/project/atlassian-api-py/
   :alt: PyPI

.. |docs-badge| image:: https://readthedocs.org/projects/atlassian-api-py/badge/?version=latest
   :target: https://atlassian-api-py.readthedocs.io/
   :alt: Documentation

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


|pypi-version| |docs-badge| |python-version| |commit-check-badge|

Overview
--------

A Python wrapper for the Atlassian REST API, supporting JIRA, Bitbucket, and Confluence. It streamlines integration with Atlassian products.

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

.. start-example

Usage
-----

You can connect to JIRA using a username and password or a token.

Using Username and Password:

.. code-block:: python

   >>> from atlassian import Jira
   >>> jira = Jira(url='https://jira.company.com', username="username", password="password")

Using a Token:

.. code-block:: python

   >>> from atlassian import Jira
   >>> jira = Jira(url='https://jira.company.com', token="yourToken")

Using a Configuration File:

Alternatively, you can store your credentials in a ``config.ini`` file:

.. code-block:: ini

   [jira]
   url = https://jira.company.com
   username = username
   password = password
   # Or
   token = yourToken

Then, you can use the configuration file to establish a connection:

.. code-block:: python

   >>> import configparser
   >>> config = configparser.ConfigParser()
   >>> config.read('config.ini')

   >>> jira_url = config['jira']['url']
   >>> jira_usr = config['jira']['username']
   >>> jira_psw = config['jira']['password']
   >>> jira_token = config['jira']['token']

Getting issue fields

Next, you can get the issue's fields as follows:

.. code-block:: python

   >>> issue = jira.issue('TEST-1')
   >>> print(issue.fields.status.name)
   Triage
   >>> print(issue.fields.description)
   this is a demo jira ticket
   >>> print(issue.fields.status.name)
   Triage
   >>> print(issue.fields.issuetype.name)
   Bug

Getting issue more fields

.. code-block:: python

   >>> print(issue.id)
   1684517
   >>> print(issue.key)
   TEST-1
   >>> print(issue.fields.assignee.key)
   xpshen
   >>> print(issue.fields.summary)
   Jira REST API Unit Test Example
   >>> ...

.. end-example

.. start-license

License
-------

This project is released under the `MIT License <LICENSE>`_.

.. end-license

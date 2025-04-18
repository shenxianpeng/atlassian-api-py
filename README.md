# Python Wrapper for Atlassian REST API

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)
[![Documentation](https://readthedocs.org/projects/atlassian-api-py/badge/?version=latest)](https://atlassian-api-py.readthedocs.io/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/atlassian-api-py?style=flat-square)](https://pypi.org/project/atlassian-api-py)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=shenxianpeng_atlassian-api-py&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=shenxianpeng_atlassian-api-py)
![PyPI - Downloads](https://img.shields.io/pypi/dw/atlassian-api-py)
[![commit-check](https://img.shields.io/badge/commit--check-enabled-brightgreen?logo=Git&logoColor=white)](https://github.com/commit-check/commit-check)

## Overview

This package is a Python wrapper for the Atlassian REST API, currently supporting JIRA and Bitbucket. It simplifies the implementation of integration with these tools.

📘 Documentation: [atlassian-api-py.readthedocs.io](https://atlassian-api-py.readthedocs.io/)

## Installation

To install the package, run the following command:

```bash
$ pip install atlassian-api-py
```

To upgrade to the latest version, use:

```bash
$ pip install atlassian-api-py --upgrade
```

**Establish connection**

You can connect to JIRA using a username and password or a token.

Using Username and Password

```python
>>> from atlassian import Jira
>>> jira = Jira(url='https://jira.company.com', username="username", password="password")
```

Using a Token

```python
>>> from atlassian import Jira
>>> jira = Jira(url='https://jira.company.com', token="yourToken")
```

Using a Configuration File

Alternatively, you can store your credentials in a `config.ini` file:

```markdown
[jira]
url = https://jira.company.com
username = username
password = password
# Or
token = yourToken
```

Then, you can use the configuration file to establish a connection:

```python
>>> import configparser
>>> config = configparser.ConfigParser()
>>> config.read('config.ini')

>>> jira_url = config['jira']['url']
>>> jira_usr = config['jira']['username']
>>> jira_psw = config['jira']['password']
>>> jira_token = config['jira']['token']
```

### Getting issue fields

Next, you can get the issue's fields as follow:

```python
>>> issue = jira.issue('TEST-1')
>>> print(issue.fields.status.name)
Triage
>>> print(issue.fields.description)
this is a demo jira ticket
>>> print(issue.fields.status.name)
Triage
>>> print(issue.fields.issuetype.name)
Bug
```

### Getting issue more fields

```python
>>> print(issue.id)
1684517
>>> print(issue.key)
TEST-1
>>> print(issue.fields.assignee.key)
xpshen
>>> print(issue.fields.summary)
Jira REST API Unit Test Example
>>> ...
```

## License

This project is released under the [MIT License](LICENSE).

# Python Wrapper for Atlassian REST API

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=shenxianpeng_atlassian-api-py&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=shenxianpeng_atlassian-api-py)
![PyPI - Downloads](https://img.shields.io/pypi/dw/atlassian-api-py)
[![commit-check](https://img.shields.io/badge/commit--check-enabled-brightgreen?logo=Git&logoColor=white)](https://github.com/commit-check/commit-check)

## What is this?

This is a package wrapper of Atlassian REST API written in Python, currently, it supports JIRA and Bitbucket.

This package was created to simplify the implementation of integration with JIRA and Bitbucket.

## QuickStart

## Install from PyPI

```bash
# install
$ pip install atlassian-api-py

# upgrade to latest
$ pip install atlassian-api-py --upgrade
```

### Establish connection

Connect with username and password

```python
>>> from atlassian import Jira
>>> jira = Jira(url='https://jira.company.com', username="username", password="password")
```

Or connect with token

```python
>>> from atlassian import Jira
>>> jira = Jira(url='https://jira.company.com', token="yourToken")
```

Or write your credentials in a configuration file `config.ini`, and get the credential though the configuration file.

```markdown
[jira]
url = https://jira.company.com
username = username
password = password
# Or
token = yourToken
```

```python
>>> import configparser
>>> config = configparser.ConfigParser()
>>> config.read('config.ini')

>>> jira_url = config['jira']['url']
>>> jira_usr = config['jira']['username']
>>> jira_psw = config['jira']['password']
>>> jira_token = config['jira']['token']
```

### Get fields

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

### More fields

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

## Unittest and Coverage

Run unittest

```bash
cd tests
python -m unittest
```

Run coverage

```bash
cd tests
coverage run -m unittest
coverage report -m              # to report on the results
coverage html                   # to get annotated HTML
```

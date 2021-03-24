# Atlassian REST API Python Wrapper

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)
[![CodeFactor](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/badge/master?s=3f5b565625069f5c5ab303a02b120197cd3abdde)](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/overview/master)
![PyPI - Downloads](https://img.shields.io/pypi/dw/atlassian-api-py)

## What is this?

This package is a wrapper of Atlassian Rest APIs written in Python, currently it supports Atlassian products: JIRA and Bitbucket.

This API package was created to bring ease of implementation for integration with JIRA and Bitbucket.

## QuickStart

```python
>>> from atlassian import Jira

>>> jira = Jira(url='https://jira.company.com', username="username", password="password")
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

Put your username and password in a configuration file `config.ini`, for example:

```markdown
[jira]
url = https://jira.company.com
username = username
password = password
```
Then get the credential information though the configuration file `config.ini`

```python
>>> import configparser
>>> config = configparser.ConfigParser()
>>> config.read('config.ini')

>>> jira_url = config['jira']['url']
>>> jira_usr = config['jira']['username']
>>> jira_psw = config['jira']['password']

>>> jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)
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

## Install from PyPI

```bash
# install
$ pip install atlassian-api-py

# upgrade
$ pip install atlassian-api-py --upgrade
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

## FAQ

### Q1: Which Jira/BitBucket version I used to develop?
> For Jira I used Jira v8.5.9 and Jira Cloud.
>
> For BitBucket I used Bitbucket v5.13.1. not support Bitbucket cloud for now.

### Q2: Are there any major changes?
> From v0.2.0 (3/9/2021), convert Get JIra API data from dict to object, no longer compatible with past old versions.


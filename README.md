# Atlassian REST API Python Wrapper

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)
[![CodeFactor](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/badge/master?s=3f5b565625069f5c5ab303a02b120197cd3abdde)](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/overview/master)
![PyPI - Downloads](https://img.shields.io/pypi/dw/atlassian-api-py)

This library is a wrapper of Atlassian Rest APIs written by Python, currently only supports JIRA and Bitbucket.

## Purpose

Create an easy to use API package that I can use for all the projects when I need CI/CD with JIRA, Bitubket.

## QuickStart

```python
>>> from atlassian import Jira

>>> jira = Jira(url='https://shenxianpeng.atlassian.net', 
... username="myusername", password="mypassword")
>>> status = jira.get_issue_status('AAP-1')
>>> print(status)
Backlog
```

Put your username and password in a configuration file `config.ini`, for example:

```markdown
[jira]
url = https://shenxianpeng.atlassian.net
username = myusername
password = mypassword
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
>>> issue = self.jira.issue('MVQA-900')
>>> print(issue.fields.description)
this is a demo jira ticket
>>> print(issue.fields.status.name)
Backlog
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


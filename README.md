# Atlassian REST API Python Wrapper

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)

This library is a wrapper of Atlassian Rest APIs written by Python, will support Jira, BitBucket, etc.

## Purpose

* In order to be better and more convenient to use.
* The pursuit of simple, lightweight, easy to use.

## QuickStart

```python
>>> from atlassian import Jira

>>> jira = Jira(url='https://shenxianpeng.atlassian.net', 
... username="myusername", password="mypassword")
>>> status = jira.get_issue_status('AAP-1')
>>> print(status)
Backlog
```
Or get credential information from a config file `config.ini`.

```markdown
[jira]
url = https://shenxianpeng.atlassian.net
username = myusername
password = mypassword
```
Then
```python
>>> import configparser
>>> config = configparser.ConfigParser()
>>> config.read('config.ini')

>>> jira_url = config['jira']['url']
>>> jira_usr = config['jira']['username']
>>> jira_psw = config['jira']['password']

>>> jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)
>>> status = jira.get_issue_status('AAP-1')
>>> print(status)
Backlog
```

## Install from PyPI

```bash
# install
$ pip install atlassian-api-py

# upgrade
$ pip install atlassian-api-py --upgrade
```

## FAQ

### Q1: Which Jira/BitBucket version I used to develop?
> For Jira I used Jira v8.5.9 and Jira Cloud.
>
> For BitBucket I used Bitbucket v5.13.1. not support Bitbucket cloud for now.


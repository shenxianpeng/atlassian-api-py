# Atlassian REST API Python Wrapper

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)

This library is a wrapper of Atlassian Rest APIs written by Python, will support Jira(In progress), BitBucket(todo), etc.

## Purpose

* In order to be better and more convenient to use.
* The pursuit of simple, lightweight, easy to use.

## QuickStart

```python
from jira import JIRA

jira = Jira(url='https://jira.atlassian.com', username='username', password='password')
status = jira.get_status('TEST-1')
print(status)
```
Or update `config.ini` first which under atlassian folder

```markdown
[jira]
url = https://jira.atlassian.com
username = username
password = password
```
Then
```python
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

jira_url = config['jira']['url']
jira_usr = config['jira']['username']
jira_psw = config['jira']['password']

jira = Jira(url=jira_url, username=jira_usr, password=jira_psw)
status = jira.get_status('TEST-1')
print(status)

```

## Install from PyPI

```bash
# install
$ pip install atlassian-api-py

# upgrade
$ pip install atlassian-api-py --upgrade
```

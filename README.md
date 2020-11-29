# Atlassian REST API Python Wrapper

![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)

This library is a wrapper of Atlassian Rest APIs written by Python, will support Jira(In progress), BitBucket(todo), etc.

## Purpose

* In order to be better and more convenient to use.
* The pursuit of simple, lightweight, easy to use.

## QuickStart

```python
from jira import JIRA

jira = Jira(url='https://jira.atlassian.com', username='username', password='password')
status = jira.get_status('TEST-001')
print(status)
```

## Install from PyPI

```bash
# install
$ pip install atlassian-api-py

# upgrade
$ pip install atlassian-api-py --upgrade
```

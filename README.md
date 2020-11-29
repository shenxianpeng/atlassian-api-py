# Atlassian Python APIs

This library is a wrapper of Atlassian Rest APIs using Python, such as Jira(In progress), BitBucket(TODO), etc.

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

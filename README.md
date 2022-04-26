# Python Wrapper for Atlassian REST API

[![PyPI](https://img.shields.io/pypi/v/atlassian-api-py)](https://pypi.org/project/atlassian-api-py/)
[![CodeFactor](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/badge/master?s=3f5b565625069f5c5ab303a02b120197cd3abdde)](https://www.codefactor.io/repository/github/shenxianpeng/atlassian-api-py/overview/master)
![PyPI - Downloads](https://img.shields.io/pypi/dw/atlassian-api-py)

## What is this?

This is a package wrapper of Atlassian REST API written in Python, currently, it only supports JIRA and Bitbucket.

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

## Changelog

Track some `minor` and `micro` changes.

* [0.3.25](https://pypi.org/project/atlassian-api-py/0.3.25/) - Apr 26, 2022 - Code format and add `Makefile` for build and test. 
* [0.3.24](https://pypi.org/project/atlassian-api-py/0.3.24/) - Apr 25, 2022 - Support search_issue_with_jql to get more than 1000 results.
* [0.3.23](https://pypi.org/project/atlassian-api-py/0.3.23/) - Jan 15, 2022 - Changed code formats with black
* [0.3.22](https://pypi.org/project/atlassian-api-py/0.3.22/) - Nov 13, 2021 - Added `update_field` in Jira.
* [0.3.21](https://pypi.org/project/atlassian-api-py/0.3.21/) - Nov 11, 2021 - Added `issue_changelog` in Jira.
* [0.3.20](https://pypi.org/project/atlassian-api-py/0.3.20/) - Nov 11, 2021 - Added `get_transitions` in Jira.
* [0.3.19](https://pypi.org/project/atlassian-api-py/0.3.19/) - Oct 7, 2021 - Added `get_user` in Bitbucket.
* [0.3.18](https://pypi.org/project/atlassian-api-py/0.3.18/) - Oct 7, 2021 - Fixed issues in bitbucket and test_bitbucket and refactor.
* [0.3.17](https://pypi.org/project/atlassian-api-py/0.3.17/) - Oct 2, 2021 - Support establish connection with token and update README.md.
* [0.3.15](https://pypi.org/project/atlassian-api-py/0.3.15/) - Sep 9, 2021 - Fixed permission issue temporarily by changing file_handler to console_handler.
* [0.3.14](https://pypi.org/project/atlassian-api-py/0.3.14/) - Sep 9, 2021 - Fixed Permission denied: 'logs' issue.
* [0.3.13](https://pypi.org/project/atlassian-api-py/0.3.13/) - Sep 8, 2021 - Added `create_issue` in Jira.
* [0.3.12](https://pypi.org/project/atlassian-api-py/0.3.12/) - Sep 2, 2021 - Added u`:` in Jira.
* [0.3.11](https://pypi.org/project/atlassian-api-py/0.3.11/) - Aug 25, 2021 - Added `get_pull_request_comments` in Bitbucket.
* [0.3.9](https://pypi.org/project/atlassian-api-py/0.3.9/) - Aug 19, 2021 - Changed `search_issue_with_sql` to `search_issue_with_jql`.
* [0.3.8](https://pypi.org/project/atlassian-api-py/0.3.8/) - Aug 19, 2021 - Changed `update_custom_field` to support pass 3 or 4 params in Jira.
* [0.3.7](https://pypi.org/project/atlassian-api-py/0.3.7/) - June 9, 2021 - Added `update_build_status` in Bitbucket.
* [0.3.6](https://pypi.org/project/atlassian-api-py/0.3.6/) - June 9, 2021 - Added `get_build_status` in Bitbucket.
* [0.3.5](https://pypi.org/project/atlassian-api-py/0.3.5/) - June 8, 2021 - Added `update_custom_field` in Jira .
* [0.3.3](https://pypi.org/project/atlassian-api-py/0.3.3/) - June 4, 2021 - Added `get_file_content` in Bitbucket.
* [0.3.0](https://pypi.org/project/atlassian-api-py/0.3.0/) - May 9, 2021 - Fixed Bitbucket and test_bitbucket issues.
* [0.2.7](https://pypi.org/project/atlassian-api-py/0.2.7/) - Apr 20, 2021 - Added create task with components in Jira.
* [0.2.5](https://pypi.org/project/atlassian-api-py/0.2.5/) - Apr 20, 2021 - Added `update_issue_component` in Jira .
* [0.2.4](https://pypi.org/project/atlassian-api-py/0.2.4/) - Mar 28, 2021 - Added create_task and refactor code for Jira.
* [0.2.0](https://pypi.org/project/atlassian-api-py/0.2.0/) - Mar 9, 2021 - Changed API return from JSON data to Python object.

## FAQ

### Q1: Which Jira/BitBucket version I used to develop?

> For Jira I used Jira v8.5.9 and Jira Cloud.
>
> For BitBucket I used Bitbucket v5.13.1. not support Bitbucket cloud for now.

### Q2: Are there any major changes?

> From [0.2.0](https://pypi.org/project/atlassian-api-py/0.2.0/) - Mar 9, 2021, convert get JIra API data from dict to object, no longer compatible with past old versions.

# Changelog

Starting from `0.5.0`, please refer to [GitHub release](https://github.com/shenxianpeng/atlassian-api-py/releases) to view release note.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - Unreleased

### Changed
- `GET` responses that are HTML pages where JSON was expected (login or SSO redirects) now raise `APIError` instead of returning the page as a string.
- **Breaking**: the import package is now `atlassian_api` (was `atlassian`). `atlassian-python-api` also ships a top-level `atlassian` package, so installing one library overwrote the other's files and uninstalling it broke the remaining one. Replace `from atlassian import ...` with `from atlassian_api import ...`.

### Added
- Atlassian Cloud support for Jira and Confluence, detected from `*.atlassian.net` / `*.jira.com` / `api.atlassian.com` URLs, or forced with the new `cloud=` argument.
  - `Jira.search_issue_with_jql()` uses `/rest/api/2/search/jql` with `nextPageToken` on Cloud (the old `/search` returns HTTP 410 there) and requests navigable fields by default, matching Server.
  - `Jira.assign_issue()` and `Jira.user()` send `accountId` on Cloud.
  - `Jira.get_projects()` collects all pages of `/project/search` on Cloud; `Jira.create_version()` sends `projectId`.
  - Confluence page, space, child-page, comment, label-listing and attachment-listing methods use the REST API v2 on Cloud, where the v1 endpoints were removed. List methods keep the v1 envelope (`results`, `start`, `limit`, `size`) and map `start`/`limit` onto v2 cursors. `/wiki` is appended to Cloud URLs.
  - A 401 on Cloud with `token=` explains that Cloud API tokens use basic auth.
- `Confluence.delete_content()` accepts `type=` (`page` or `blogpost`), used on Cloud.
- Errors raise status-specific subclasses of `APIError` (all still caught by `except APIError`): `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`, `ConflictError`, `RateLimitError` (with `retry_after`) and `ServerError`.
- Automatic retries for HTTP 429 (any method) and 503 (`GET`), honouring `Retry-After` (seconds or HTTP date). New `max_retries` (default 3) and `max_retry_wait` (default 60 s) arguments; a longer `Retry-After` raises `RateLimitError` instead of sleeping.
- `AtlassianAPI.request()` accepts `files=`, `headers=` (per request) and `stream=`.
- Jira: `iter_issues()` (generator over all pages, Server and Cloud), `count_issues()`, `update_issue()`, `get_fields()`, `get_field_id()`, `search_users()`, `add_worklog()`, `get_worklogs()`, `add_attachment()`, `get_attachment()`, `download_attachment()`, `delete_attachment()`.
- Confluence: `iter_search()` (CQL over all pages), `create_or_update_page()`, `download_attachment()`, `export_page_pdf()` (Server/Data Center).
- Bitbucket: `get_default_branch()`, `get_webhooks()`, `create_webhook()`, `delete_webhook()`, `get_repo_permissions()`, `set_repo_permission()`, `revoke_repo_permission()`, `list_files()`, `compare_commits()`, `compare_changes()`.
- Downloads can stream to a file (`path=`) instead of loading the whole file into memory.

### Removed
- `Jira.create_task()` and `Jira.create_sub_task()` (deprecated in 1.0.0); use `Jira.create_issue()`.
- `Bitbucket` now raises `ValueError` for Bitbucket Cloud (`bitbucket.org`) URLs instead of sending Server API calls there.

## [1.0.1] - Unreleased

### Fixed
- `Bitbucket.get_file_change_history()` no longer loops forever on multi-page results: the URL hard-coded `start=0`, so every follow-up request asked for the first page again.
- `Bitbucket.get_merged_branch()` no longer compares against a hard-coded `master`; it uses the repository's default branch, or the new `base_branch` argument.
- `limit` on paginated Bitbucket methods is now a real cap on the number of results (it could return more, and sent `limit=0` requests).
- Query parameters are URL-encoded: branch names, usernames, PR states and issue IDs containing `+`, `&`, `#` or spaces were sent mangled (`Bitbucket.get_branch_commits()`, `get_pull_request()`, `get_file_change_history()`, `get_file_content()`, `Jira.user()`, `Jira.get_dev_status()`).
- `Jira.assign_issue(key)` without an assignee now unassigns the issue as documented; it used to send `-1`, which Jira treats as "automatic assignee". Pass `"-1"` explicitly for that.
- The library no longer prints log lines to stdout by itself, and its records now reach the application's logging configuration (`logging.basicConfig(level=logging.DEBUG)` shows request logs). Only a `NullHandler` is attached.
- `Confluence.upload_attachment()` sends `X-Atlassian-Token` on the upload request only, instead of setting it on the shared session, so concurrent requests are not affected.

## [1.0.0] - 2026-04-11

### Added
- `atlassian.__version__` attribute for runtime version inspection (PEP 396).
- `atlassian/py.typed` marker file to declare inline type information (PEP 561).
- `verify` and `proxies` parameters to `AtlassianAPI.__init__()` for SSL certificate control and proxy support.
- `Confluence.get_page_by_title(space_key, title)` — find a page by its title within a space.
- `Confluence.upload_attachment(page_id, filename, file_data)` — attach a file to a page.
- `Confluence.get_comments(page_id)` — retrieve comments on a page.
- `Confluence.add_comment(page_id, body)` — post a comment on a page.
- `fields` parameter to `Jira.search_issue_with_jql()` — callers can now specify which fields to return; defaults to `None` (all fields).
- `version` parameter to `Confluence.update_content()` — callers can supply an explicit version; when omitted the current version is fetched automatically.

### Changed
- **Breaking**: `Confluence.update_content()` now fetches the current page version from the API and submits `current_version + 1` instead of always submitting version `2`.
- `Jira.issue_changelog()` now passes query parameters via `params=` dict instead of URL string splicing, consistent with the rest of the library.
- `Jira.search_issue_with_jql()` no longer hard-codes `["summary", "status", "issuetype", "fixVersions"]`; omitting `fields` returns all fields from the API.

### Deprecated
- `Jira.create_task()` — emits `DeprecationWarning`; use `create_issue()` instead. Will be removed in a future version.
- `Jira.create_sub_task()` — emits `DeprecationWarning`; use `create_issue()` instead. Will be removed in a future version.

* [0.5.0](https://pypi.org/project/atlassian-api-py/0.5.0/) - Apr 10, 2023
* [0.4.0](https://pypi.org/project/atlassian-api-py/0.4.0/) - Apr 26, 2022 - Code format and add `Makefile` for build and test.
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

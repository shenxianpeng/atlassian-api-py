# GitHub Copilot Instructions for atlassian-api-py

## Project Overview

This is a Python wrapper for Atlassian REST APIs, supporting JIRA, Bitbucket, and Confluence. The project streamlines integration with Atlassian products.

## Code Style and Standards

### Formatting and Linting
- **Python formatter**: Use [Black](https://github.com/psf/black) for code formatting
- **Type checking**: Use [mypy](https://mypy.readthedocs.io/) for static type checking
- **Pre-commit hooks**: All code must pass pre-commit checks before committing
- Run linting with: `nox -s lint`

### Code Standards
- Follow PEP 8 style guidelines (enforced by Black)
- Add type hints to all function signatures
- Use docstrings for all public classes and methods (Google-style docstrings)
- Maintain consistent error handling using the `atlassian.error` module
- Use the logger from `atlassian.logger` for logging operations

### API Method Conventions
- Method names use snake_case (e.g., `issue_changelog`, `update_issue_label`)
- Parameters use descriptive names matching Atlassian API terminology
- Resource methods follow pattern: `{action}_{resource}` (e.g., `get_content`, `create_branch`, `delete_issue_link`)
- Update methods typically accept optional `add_*` and `remove_*` parameters for list fields
- URL construction uses f-strings: `f"/rest/api/2/issue/{issue_key}"`
- Return `{}` or `None` for empty responses using `or {}` / `or None` pattern

## Development Environment

### Supported Python Versions
- Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- All changes must be compatible with Python 3.9+

### Dependencies
- Core: `requests` library for HTTP operations
- Dev dependencies include: `nox`, `pre-commit`, `mypy`, `twine`
- Test dependencies: `pytest`, `coverage`
- Documentation: `myst-parser`, `sphinx`, `sphinx_rtd_theme`, `sphinx-autobuild`

## Build and Test Process

### Build Commands
Use [nox](https://nox.thea.codes/) for all development tasks:

- **Lint code**: `nox -s lint`
- **Build wheel**: `nox -s build`
- **Install built wheel**: `nox -s install`
- **Run tests**: `nox -s test` (runs across all Python versions)
- **Run tests for specific version**: `nox -s test-3.12`
- **Generate coverage**: `nox -s coverage`
- **Build docs**: `nox -s docs`
- **Live docs server**: `nox -s docs-live`

### Testing Guidelines
- Tests are located in the `tests/` directory
- Test files follow the pattern `test_*.py`
- Use pytest for testing with class-based test organization
- Maintain or improve code coverage
- Test structure mirrors the main package:
  - [test_jira.py](tests/test_jira.py) for JIRA functionality
  - [test_confluence.py](tests/test_confluence.py) for Confluence functionality
  - [test_bitbucket.py](tests/test_bitbucket.py) for Bitbucket functionality

#### Testing Patterns
- Use `@pytest.fixture` to create test instances
- Mock HTTP methods (`get`, `post`, `put`, `delete`) with `unittest.mock.MagicMock`
- Test method calls by inspecting `call_args` on mocked methods
- Use `SimpleNamespace` for mocking complex response objects (see [test_bitbucket.py](tests/test_bitbucket.py#L21-L23))
- Example test fixture pattern from [test_jira.py](tests/test_jira.py#L7-L13):
  ```python
  @pytest.fixture
  def jira(self):
      jira_client = Jira(url="https://fake_url")
      jira_client.get = MagicMock()
      return jira_client
  ```

## Project Structure

```
atlassian-api-py/
├── atlassian/          # Main package
│   ├── __init__.py
│   ├── client.py       # Base AtlassianAPI client
│   ├── jira.py         # JIRA API wrapper
│   ├── confluence.py   # Confluence API wrapper
│   ├── bitbucket.py    # Bitbucket API wrapper
│   ├── error.py        # Error handling
│   └── logger.py       # Logging utilities
├── tests/              # Test suite
├── docs/               # Sphinx documentation
├── noxfile.py          # Nox automation
└── pyproject.toml      # Project configuration
```

## Architecture Patterns

### API Client Pattern
All API classes (`Jira`, `Confluence`, `Bitbucket`) inherit from `AtlassianAPI` in [client.py](atlassian/client.py):
- Base class constructor supports multiple authentication methods:
  - Basic auth: `username` + `password` parameters
  - Bearer token: `token` parameter
  - Custom session: `session` parameter
- Context manager support: use `with Jira(...) as jira:` pattern
- Session management with `requests.Session` for connection pooling
- Standard HTTP methods: `get()`, `post()`, `put()`, `delete()`, `request()`

### Request/Response Patterns
- **GET requests**: Return `SimpleNamespace` objects (access with dot notation: `issue.fields.status.name`)
- **POST/PUT/DELETE**: Return dictionaries or `None`
- Response handler (`_response_handler`) safely parses JSON responses
- Empty responses return `None` or `{}` depending on the method
- URL patterns follow `/rest/api/{version}/{resource}/{id}` format

### Authentication Implementation
Example from [client.py](atlassian/client.py#L43-L53):
```python
if username and password:
    self._create_basic_session(username, password)
elif token is not None:
    self._create_token_session(token)
```

### Pagination Pattern (Bitbucket-specific)
Bitbucket API uses `_get_paged()` helper in [bitbucket.py](atlassian/bitbucket.py#L12-L36):
- Handles paginated responses with `isLastPage` and `nextPageStart`
- Supports optional `limit` parameter to cap result count
- Returns aggregated list of all paginated values

### Error Handling
- Custom `APIError` exception in [error.py](atlassian/error.py#L52-L87)
- Maps HTTP status codes to human-readable messages
- Logger disabled by default in client (`logger.disabled = True`)
- Log errors using `from atlassian.logger import get_logger`

## Documentation

- Documentation is built with Sphinx
- Supports both reStructuredText (.rst) and Markdown (.md) formats via myst-parser
- Current documentation primarily uses .rst format
- Hosted on ReadTheDocs: https://atlassian-api-py.readthedocs.io/
- Update documentation when adding new features or changing APIs
- Build docs locally: `nox -s docs`

## Contributing Guidelines

When making changes:
1. Ensure code passes linting: `nox -s lint`
2. Add or update tests for new functionality
3. Run the test suite: `nox -s test`
4. Update documentation if adding public APIs
5. Follow semantic versioning for releases
6. Update CHANGELOG.md with notable changes

## Common Commands

```bash
# Install development dependencies
pip install -e ".[dev,test,docs]"

# Run pre-commit hooks manually
pre-commit run --all-files

# Run specific test file
pytest tests/test_jira.py

# Generate and view coverage report
nox -s coverage
```

## Additional Context

- The project uses `setuptools-scm` for versioning
- Version is determined from git tags
- License: MIT License
- The project adheres to semantic versioning
- Changelog format follows [Keep a Changelog](https://keepachangelog.com/)

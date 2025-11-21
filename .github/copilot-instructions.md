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
- Use pytest for testing
- Maintain or improve code coverage
- Test structure mirrors the main package:
  - `test_jira.py` for JIRA functionality
  - `test_confluence.py` for Confluence functionality
  - `test_bitbucket.py` for Bitbucket functionality

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
- All API classes inherit from `AtlassianAPI` base class in `client.py`
- Base class handles common functionality (authentication, HTTP requests)
- Each service (JIRA, Confluence, Bitbucket) has its own class
- Methods return Python dictionaries or lists, not raw JSON

### Error Handling
- Use custom exceptions from `atlassian.error` module
- Handle HTTP errors appropriately
- Log errors using the project's logger

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

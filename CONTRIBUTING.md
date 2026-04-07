# Contributing to atlassian-api-py

Thank you for your interest in contributing! We welcome bug reports, feature requests, documentation improvements, and code contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this standard.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/atlassian-api-py.git
   cd atlassian-api-py
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/shenxianpeng/atlassian-api-py.git
   ```

## Development Setup

Install the package in editable mode with all development, test, and docs extras:

```bash
pip install -e ".[dev,test,docs]"
```

Install pre-commit hooks (required before your first commit):

```bash
pre-commit install
```

We use [nox](https://nox.thea.codes/) to automate development tasks:

| Command | Description |
|---------|-------------|
| `nox -s lint` | Run linters (Black, mypy, bandit) |
| `nox -s test` | Run the full test suite across all supported Python versions |
| `nox -s test-3.12` | Run tests for a specific Python version |
| `nox -s coverage` | Generate a coverage report |
| `nox -s docs` | Build the documentation |

## Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b my-feature-or-fix
   ```
2. Write your code following the style guidelines below.
3. Add or update tests in the `tests/` directory.
4. Update documentation in `docs/` if your change affects the public API.
5. Run linting and tests before pushing (see below).

### Code Style

- **Formatter**: [Black](https://github.com/psf/black) — run `nox -s lint` to apply automatically.
- **Type hints**: All public functions and methods must have type annotations.
- **Docstrings**: Use Google-style docstrings for all public classes and methods.
- **Naming**: Method names use `snake_case`; API methods follow the pattern `{action}_{resource}` (e.g., `get_issue`, `create_branch`).

## Running Tests

```bash
# Run tests for the current Python version
nox -s test-3.12

# Run the full matrix (all supported Python versions)
nox -s test
```

Tests live in `tests/` and mirror the package structure:

- `tests/test_jira.py` — Jira API tests
- `tests/test_bitbucket.py` — Bitbucket API tests
- `tests/test_confluence.py` — Confluence API tests

Use `unittest.mock.MagicMock` to mock HTTP calls (see existing tests for examples).

## Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin my-feature-or-fix
   ```
2. Open a Pull Request against the `main` branch.
3. Fill in the PR template — describe what changed and why.
4. Ensure all CI checks pass.
5. Address any review comments promptly.

## Reporting Bugs

Please use the [Bug Report](https://github.com/shenxianpeng/atlassian-api-py/issues/new?template=bug_report.md) issue template and include:

- A minimal reproducible example.
- Your OS, Python version, and `atlassian-api-py` version.
- The full error message and stack trace.

## Requesting Features

Please use the [Feature Request](https://github.com/shenxianpeng/atlassian-api-py/issues/new?template=feature_request.md) issue template and describe the problem you're trying to solve.

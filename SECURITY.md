# Security Policy

`atlassian-api-py` is given Jira, Confluence and Bitbucket credentials, so
problems in how it handles them are treated as security issues. Examples:

- credentials sent to a host other than the one in the client's `url`
- credentials, tokens or response bodies with secrets written to logs
- a server response that makes the client write outside the path it was given

## Supported Versions

Only the latest release receives security fixes.

| Version        | Supported          |
| -------------- | ------------------ |
| latest release | :white_check_mark: |
| older releases | :x:                |

## Reporting a Vulnerability

Please **do not** open a public issue to report a security vulnerability.

Instead, report it privately through GitHub's
[Security Advisories](https://github.com/shenxianpeng/atlassian-api-py/security/advisories/new)
feature (click **Report a vulnerability**).

You can expect:

- An acknowledgement within **48 hours**.
- A status update within **7 days** indicating whether the vulnerability has been accepted or declined.
- A patch or mitigation, followed by a public disclosure after the fix has been released.

## Verifying a Release

Releases are uploaded to PyPI by the
[`publish-pypi.yml`](.github/workflows/publish-pypi.yml) workflow using
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/), with no
long-lived API token. Files uploaded this way carry an
[attestation](https://docs.pypi.org/attestations/) that links them to this
repository and the commit they were built from.

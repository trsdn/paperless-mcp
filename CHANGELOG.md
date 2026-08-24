# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Fixed

- A manual `workflow_dispatch` run of the release workflow no longer attempts to
  publish. PyPI rejects re-uploading an existing version, so dispatching without
  a new tag always failed at the upload step. `publish` and `github-release` are
  now restricted to tag pushes, which turns a manual run into a safe dry run of
  the build and quality gates.

## [0.1.3] - 2026-08-24

### Changed

- Restricted the sdist to the package source, `README.md`, `CHANGELOG.md`,
  `LICENSE`, and `pyproject.toml`. Previously the source distribution also
  shipped `tests/`, `deploy/` (including the environment example), the
  `.github/` workflows, and `uv.lock`.
- Raised the release workflow to `actions/upload-artifact@v7` and
  `actions/download-artifact@v8`, matching the action majors already used
  elsewhere in the repository.

## [0.1.2] - 2026-08-24

### Added

- Published on PyPI as `trsdn-paperless-mcp` via GitHub Actions Trusted
  Publishing (OIDC, environment `pypi`, no API tokens). The release workflow now
  builds distributions, validates them with `twine check`, and publishes them
  before creating the GitHub release.
- `python -m paperless_mcp` now starts the server, alongside the existing
  `paperless-mcp` console script.

### Changed

- Renamed the PyPI distribution to `trsdn-paperless-mcp` because
  `paperless-mcp` is taken by an unrelated project. The import name
  (`paperless_mcp`) and the command name (`paperless-mcp`) are unchanged.

### Security

- Upgraded FastMCP to 3.4.7, resolving an SSRF and path traversal issue in the
  OpenAPI provider (critical), missing consent verification in the OAuth proxy
  callback (high), and a command injection issue (medium).
- Upgraded pytest to 9.1.1, resolving vulnerable `tmpdir` handling (medium).
- Dropped the transitive `diskcache` dependency, which carried an unpatched
  unsafe pickle deserialization issue (medium).

### Changed

- Migrated to the FastMCP 3.x API: tool discovery now uses `list_tools()`, and
  `@mcp.tool` returns the original function, so tests call tools directly
  instead of through the removed `.fn` accessor.
- Raised the development dependency floor to `pytest-cov>=7.1.0`.
- Upgraded `actions/checkout` to v7 and `gitleaks/gitleaks-action` to v3, moving
  every workflow action onto the Node 24 runtime before GitHub removes Node 20
  from hosted runners on 2026-09-16.
- Pinned `astral-sh/setup-uv` to the immutable tag `v10.0.1`. The action stopped
  publishing major tags after v7, so the previous `@v7` reference could never be
  updated automatically.

## [0.1.1] - 2026-08-20

### Added

- Professional project metadata, repository badges, and expanded setup documentation.
- Python 3.14 CI coverage and an enforced Ruff formatting check.
- Tag-driven GitHub releases containing wheel and source distributions.
- Issue forms, a pull request template, a code of conduct, and Dependabot configuration.

### Changed

- Reformatted Python sources and tests with Ruff without changing runtime behavior.

## [0.1.0] - 2026-08-20

### Added

- Streamable HTTP MCP server with static bearer-token authentication.
- Eight tools for searching, reading, downloading, listing metadata, updating,
  and uploading Paperless-ngx documents.
- Optional read-only mode for disabling update and upload tools.
- systemd deployment files and installation script.
- Tests for configuration, authentication, tool behavior, and write blocking.
- CI for Python 3.11 through 3.13 and full-history secret scanning.

[Unreleased]: https://github.com/trsdn/paperless-mcp/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/trsdn/paperless-mcp/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/trsdn/paperless-mcp/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/trsdn/paperless-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/trsdn/paperless-mcp/releases/tag/v0.1.0

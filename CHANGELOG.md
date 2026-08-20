# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

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

[Unreleased]: https://github.com/trsdn/paperless-mcp/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/trsdn/paperless-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/trsdn/paperless-mcp/releases/tag/v0.1.0

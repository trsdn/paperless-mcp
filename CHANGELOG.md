# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

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

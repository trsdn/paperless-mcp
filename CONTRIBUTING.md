# Contributing

Issues and pull requests are welcome. Keep changes focused and avoid including
real Paperless documents, OCR text, tokens, internal hostnames, private IP
addresses, or local filesystem paths in reports, fixtures, and logs.

## Development setup

Requirements:

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run pytest --cov=paperless_mcp --cov-fail-under=85
uv build
```

Tests must not require a live Paperless-ngx instance. Use test-only URLs and
credentials such as the reserved `example.test` domain.

## Pull requests

Describe the user-visible behavior and security implications of the change.
Add or update tests for behavior changes, keep the eight-tool MCP contract
backward compatible unless the change is explicitly breaking, and update the
README or changelog when appropriate.

Run the complete local checks before opening a pull request. CI validates
Python 3.11 through 3.13 and scans the repository for secrets.

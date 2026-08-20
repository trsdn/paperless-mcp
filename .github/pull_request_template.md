## Summary

Describe the problem and the outcome of this change.

## Validation

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run pytest --cov=paperless_mcp --cov-fail-under=85`
- [ ] `uv build`

## Security and privacy

- [ ] Tests use mocked requests and do not access a live Paperless-ngx instance.
- [ ] The change introduces no documents, OCR text, credentials, hostnames, private IP addresses, or local deployment paths.
- [ ] I documented changes to authentication, document access, write behavior, or the MCP tool contract.
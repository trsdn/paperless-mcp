# Security Policy

## Supported versions

Security fixes are provided for the latest published release.

## Reporting a vulnerability

Please report suspected vulnerabilities through a private GitHub Security
Advisory for this repository. Do not open a public issue containing exploit
steps, tokens, document content, or deployment details.

Include the affected version, impact, reproduction steps, and any suggested
mitigation. You can expect an initial response within seven days.

## Security boundary

paperless-mcp uses a static bearer token to authenticate MCP clients and a
Paperless API token to access Paperless-ngx. It does not provide user-level
authorization, multi-tenancy, rate limiting, OAuth/OIDC, or public-internet
hardening.

Deploy it only on a trusted private network, restrict inbound access, and use a
maintained TLS reverse proxy when traffic crosses an untrusted network. Start
with `PAPERLESS_READ_ONLY=1`; enable write tools only for trusted clients that
require them.

Treat both tokens as secrets. Use independent, randomly generated values,
store them outside the repository, limit access to the environment file, and
rotate them after suspected exposure.

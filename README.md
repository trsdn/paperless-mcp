# paperless-mcp

[![CI](https://github.com/trsdn/paperless-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/trsdn/paperless-mcp/actions/workflows/ci.yml)
[![Secret scan](https://github.com/trsdn/paperless-mcp/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/trsdn/paperless-mcp/actions/workflows/secret-scan.yml)
[![Release](https://img.shields.io/github/v/release/trsdn/paperless-mcp)](https://github.com/trsdn/paperless-mcp/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.11--3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/trsdn/paperless-mcp)](LICENSE)

An authenticated [Model Context Protocol](https://modelcontextprotocol.io/)
server that exposes a
[Paperless-ngx](https://docs.paperless-ngx.com/) instance over streamable HTTP
with static bearer-token authentication, built with
[FastMCP](https://github.com/PrefectHQ/fastmcp).

**Use it to:** search and read archived documents, inspect Paperless metadata,
download files, update document properties, and upload new documents from any
HTTP-capable MCP client.

## Why Paperless MCP?

- **Useful document access:** eight focused tools cover retrieval, metadata,
  downloads, updates, and ingestion.
- **Read-only mode:** one environment variable disables every mutating tool.
- **Authenticated transport:** every MCP request requires a dedicated bearer
  token independent from the Paperless API token.
- **Self-hosted deployment:** runs beside Paperless-ngx or on another private
  Linux host with the included systemd unit.
- **No live-instance tests:** the test suite uses mocked HTTP requests and
  never needs access to real documents.

> [!IMPORTANT]
> Start with `PAPERLESS_READ_ONLY=1` unless clients need to update metadata or
> upload documents. This server is intended for trusted private networks. The
> built-in static token authentication is not sufficient public-internet
> hardening by itself.

## Quick Start

Requirements: Python 3.11 or newer, a reachable Paperless-ngx instance, and
[uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/trsdn/paperless-mcp.git
cd paperless-mcp
uv sync --locked --no-dev

export PAPERLESS_URL=http://127.0.0.1:8000
export PAPERLESS_TOKEN=your-paperless-api-token
export PAPERLESS_MCP_TOKEN="$(openssl rand -hex 32)"
export PAPERLESS_READ_ONLY=1
uv run paperless-mcp
```

The server listens on `http://0.0.0.0:8770/mcp` by default. Keep the generated
MCP token secret and configure the same value in the client.

## Available Tools

| Tool | Access | Purpose |
| --- | --- | --- |
| `search_documents` | Read | Full-text and filtered document search |
| `get_document` | Read | Return metadata and optional OCR content |
| `download_document` | Read | Return an archived or original file as base64 |
| `list_tags` | Read | List Paperless tags |
| `list_correspondents` | Read | List Paperless correspondents |
| `list_document_types` | Read | List Paperless document types |
| `update_document` | Write | Update title, correspondent, type, or tags |
| `upload_document` | Write | Upload a file to the consume pipeline |

`update_document` and `upload_document` are disabled when
`PAPERLESS_READ_ONLY=1`. The compatibility default remains `0`, so set the
variable explicitly for a read-only deployment.

## Configuration

All configuration is via environment variables — see
[`deploy/paperless-mcp.env.example`](deploy/paperless-mcp.env.example).

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PAPERLESS_URL` | yes | none | Base URL, e.g. `http://127.0.0.1:8000` |
| `PAPERLESS_TOKEN` | yes | none | Paperless API token (Settings > API Tokens) |
| `PAPERLESS_MCP_TOKEN` | yes | none | Bearer token clients must send |
| `PAPERLESS_MCP_HOST` | no | `0.0.0.0` | Bind host |
| `PAPERLESS_MCP_PORT` | no | `8770` | Bind port |
| `PAPERLESS_MCP_PATH` | no | `/mcp` | HTTP path |
| `PAPERLESS_READ_ONLY` | no | `0` | Set `1` to disable writes |

## Linux Service

```bash
curl -fsSLO https://raw.githubusercontent.com/trsdn/paperless-mcp/main/deploy/install.sh
less install.sh
sudo bash install.sh
sudoedit /etc/paperless-mcp/env
systemctl enable --now paperless-mcp
journalctl -u paperless-mcp -f
```

Generate a dedicated bearer token before editing the environment file:

```bash
openssl rand -hex 32
```

## Development

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=paperless_mcp --cov-fail-under=85
uv build
```

Tests use mocked HTTP requests and never require a live Paperless-ngx instance.
CI runs on Python 3.11, 3.12, 3.13, and 3.14.

## Client config

### Claude Desktop

Claude Desktop currently only speaks MCP over **stdio**, so use the
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote) bridge:

```jsonc
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "paperless": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://paperless-mcp.example.com/mcp",
        "--header",
        "Authorization: Bearer YOUR_PAPERLESS_MCP_TOKEN"
      ]
    }
  }
}
```

### VS Code (`mcp.json`)

```jsonc
{
  "servers": {
    "paperless": {
      "type": "http",
      "url": "https://paperless-mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_PAPERLESS_MCP_TOKEN"
      }
    }
  }
}
```

## Security Model

- Prefer `PAPERLESS_READ_ONLY=1`. Enable writes only for clients that require
  them and that you trust with document access.
- Do not expose port 8770 directly to the public internet. Restrict network
  access and place the service behind a maintained reverse proxy with TLS.
- Use long, independent values for the Paperless API token and MCP bearer
  token. Never commit either token.
- The bearer token only protects the MCP layer. The Paperless API token
  stored in `/etc/paperless-mcp/env` carries full account permissions, so the
  file is `0640`, owned by `paperless-mcp`.
- To rotate the bearer token: edit `/etc/paperless-mcp/env`, then
  `systemctl restart paperless-mcp`.
- See [SECURITY.md](SECURITY.md) for vulnerability reporting and the supported
  security boundary.

## Project

- [Releases](https://github.com/trsdn/paperless-mcp/releases)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Issue tracker](https://github.com/trsdn/paperless-mcp/issues)

Licensed under the [MIT License](LICENSE).

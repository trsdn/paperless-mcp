# paperless-mcp

A small [MCP](https://modelcontextprotocol.io/) server that exposes a
[Paperless-ngx](https://docs.paperless-ngx.com/) instance over streamable HTTP
with static bearer-token authentication, built with
[FastMCP](https://github.com/PrefectHQ/fastmcp).

It can run on the Paperless-ngx host or another private-network Linux host as a
systemd service. MCP clients can then search, read, tag, and upload documents.

> [!IMPORTANT]
> Start with `PAPERLESS_READ_ONLY=1` unless clients need to update metadata or
> upload documents. This server is intended for trusted private networks. The
> built-in static token authentication is not sufficient public-internet
> hardening by itself.

## Tools

| Tool | Purpose |
| --- | --- |
| `search_documents` | Full-text + filter search (tags, correspondent, type, date) |
| `get_document` | Metadata + OCR content for one document |
| `download_document` | Download archived or original file (base64) |
| `list_tags` | All Paperless tags |
| `list_correspondents` | All Paperless correspondents |
| `list_document_types` | All Paperless document types |
| `update_document` | Patch title, correspondent, type, add/remove/replace tags |
| `upload_document` | Upload a new file to the consume pipeline |

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

## Install on Linux with systemd

```bash
curl -fsSLO https://raw.githubusercontent.com/trsdn/paperless-mcp/main/deploy/install.sh
less install.sh
sudo bash install.sh
sudoedit /etc/paperless-mcp/env
systemctl enable --now paperless-mcp
journalctl -u paperless-mcp -f
```

Generate the bearer token once:

```bash
openssl rand -hex 32
```

## Local development

```bash
uv sync
export PAPERLESS_URL=http://127.0.0.1:8000
export PAPERLESS_TOKEN=...        # Paperless API token
export PAPERLESS_MCP_TOKEN=devtoken
export PAPERLESS_READ_ONLY=1
uv run paperless-mcp
```

Run the quality checks with:

```bash
uv run ruff check .
uv run pytest --cov=paperless_mcp --cov-fail-under=85
uv build
```

The server listens on `http://0.0.0.0:8770/mcp`.

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

## Security notes

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

## License

MIT

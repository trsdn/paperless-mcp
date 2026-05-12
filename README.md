# paperless-mcp

A small [MCP](https://modelcontextprotocol.io/) server that exposes a
[Paperless-ngx](https://docs.paperless-ngx.com/) instance over **HTTP** with
**static bearer-token** auth, built with
[FastMCP](https://github.com/PrefectHQ/fastmcp).

Designed to run **inside the Paperless-ngx LXC** (192.168.2.23 / LXC 106) as a
systemd service so that Claude Desktop, VS Code, and other MCP clients can
search, read, tag, and upload documents remotely.

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
`PAPERLESS_READ_ONLY=1`.

## Configuration

All configuration is via environment variables — see
[`deploy/paperless-mcp.env.example`](deploy/paperless-mcp.env.example).

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PAPERLESS_URL` | yes | — | Base URL, e.g. `http://127.0.0.1:8000` |
| `PAPERLESS_TOKEN` | yes | — | Paperless API token (Settings → API Tokens) |
| `PAPERLESS_MCP_TOKEN` | yes | — | Bearer token clients must send |
| `PAPERLESS_MCP_HOST` | no | `0.0.0.0` | Bind host |
| `PAPERLESS_MCP_PORT` | no | `8770` | Bind port |
| `PAPERLESS_MCP_PATH` | no | `/mcp` | HTTP path |
| `PAPERLESS_READ_ONLY` | no | `0` | Set `1` to disable writes |

## Install on the Paperless LXC

```bash
ssh root@192.168.2.23
curl -fsSL https://raw.githubusercontent.com/trsdn/paperless-mcp/main/deploy/install.sh | bash
nano /etc/paperless-mcp/env        # paste tokens
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
export PAPERLESS_URL=http://192.168.2.23:8000
export PAPERLESS_TOKEN=...        # Paperless API token
export PAPERLESS_MCP_TOKEN=devtoken
uv run paperless-mcp
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
        "http://192.168.2.23:8770/mcp",
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
      "url": "http://192.168.2.23:8770/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_PAPERLESS_MCP_TOKEN"
      }
    }
  }
}
```

## Security notes

- Do **not** expose port 8770 to the public internet without a reverse proxy
  + TLS. On the trusted home LAN, the static bearer token is acceptable.
- The bearer token only protects the MCP layer. The Paperless API token
  stored in `/etc/paperless-mcp/env` carries full account permissions, so the
  file is `0640`, owned by `paperless-mcp`.
- To rotate the bearer token: edit `/etc/paperless-mcp/env`, then
  `systemctl restart paperless-mcp`.

## License

MIT

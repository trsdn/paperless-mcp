#!/usr/bin/env bash
# Install paperless-mcp on the Paperless-ngx LXC (192.168.2.23 / LXC 106).
# Usage:  sudo bash install.sh
set -euo pipefail

REPO="${REPO:-https://github.com/trsdn/paperless-mcp.git}"
TARGET="${TARGET:-/opt/paperless-mcp}"
ENV_DIR="${ENV_DIR:-/etc/paperless-mcp}"
LOG_DIR="${LOG_DIR:-/var/log/paperless-mcp}"

echo "==> Installing dependencies"
apt-get update -qq
apt-get install -y --no-install-recommends git curl ca-certificates python3-venv

echo "==> Creating system user"
id -u paperless-mcp >/dev/null 2>&1 || useradd --system --home "$TARGET" --shell /usr/sbin/nologin paperless-mcp

echo "==> Cloning into $TARGET"
if [ ! -d "$TARGET/.git" ]; then
  git clone "$REPO" "$TARGET"
else
  git -C "$TARGET" pull --ff-only
fi

echo "==> Installing uv"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "==> Building venv"
cd "$TARGET"
uv sync
chown -R paperless-mcp:paperless-mcp "$TARGET"

echo "==> Setting up env + logs"
install -d -m 0750 -o paperless-mcp -g paperless-mcp "$ENV_DIR"
install -d -m 0755 -o paperless-mcp -g paperless-mcp "$LOG_DIR"
if [ ! -f "$ENV_DIR/env" ]; then
  install -m 0640 -o paperless-mcp -g paperless-mcp \
    "$TARGET/deploy/paperless-mcp.env.example" "$ENV_DIR/env"
  echo "    -> wrote $ENV_DIR/env (PLEASE EDIT TOKENS BEFORE STARTING)"
fi

echo "==> Installing systemd unit"
install -m 0644 "$TARGET/deploy/paperless-mcp.service" /etc/systemd/system/paperless-mcp.service
systemctl daemon-reload

echo
echo "Done. Next steps:"
echo "  1. nano $ENV_DIR/env       # set PAPERLESS_TOKEN and PAPERLESS_MCP_TOKEN"
echo "  2. systemctl enable --now paperless-mcp"
echo "  3. journalctl -u paperless-mcp -f"

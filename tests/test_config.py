import pytest

from paperless_mcp import server

REQUIRED_ENV = ("PAPERLESS_URL", "PAPERLESS_TOKEN", "PAPERLESS_MCP_TOKEN")


def test_module_import_does_not_require_environment(monkeypatch):
    for name in REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)

    server.CONFIG = None

    with pytest.raises(RuntimeError, match="Missing required env var: PAPERLESS_URL"):
        server.get_config()


def test_get_config_loads_and_caches_environment(monkeypatch):
    monkeypatch.setenv("PAPERLESS_URL", "http://paperless.example.test/")
    monkeypatch.setenv("PAPERLESS_TOKEN", "paperless-test-token")
    monkeypatch.setenv("PAPERLESS_MCP_TOKEN", "mcp-test-token")
    monkeypatch.setenv("PAPERLESS_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("PAPERLESS_MCP_PORT", "9876")
    monkeypatch.setenv("PAPERLESS_MCP_PATH", "/test-mcp")
    monkeypatch.setenv("PAPERLESS_READ_ONLY", "true")
    server.CONFIG = None

    config = server.get_config()

    assert config.paperless_url == "http://paperless.example.test"
    assert config.paperless_token == "paperless-test-token"
    assert config.mcp_token == "mcp-test-token"
    assert config.host == "127.0.0.1"
    assert config.port == 9876
    assert config.path == "/test-mcp"
    assert config.read_only is True
    assert server.get_config() is config

import pytest

from paperless_mcp import server


@pytest.fixture(autouse=True)
def reset_config():
    server.CONFIG = None
    yield
    server.CONFIG = None


@pytest.fixture
def config():
    value = server.Config(
        paperless_url="http://paperless.example.test",
        paperless_token="paperless-test-token",
        mcp_token="mcp-test-token",
        host="127.0.0.1",
        port=8770,
        path="/mcp",
        read_only=False,
    )
    server.CONFIG = value
    return value
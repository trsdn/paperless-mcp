from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from paperless_mcp.server import BearerAuthMiddleware


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def test_bearer_auth_rejects_missing_and_wrong_tokens(config):
    app = Starlette(
        routes=[Route("/health", health)],
        middleware=[Middleware(BearerAuthMiddleware)],
    )

    with TestClient(app) as client:
        assert client.get("/health").status_code == 401
        assert client.get(
            "/health", headers={"Authorization": "Bearer wrong-token"}
        ).status_code == 401


def test_bearer_auth_allows_matching_token(config):
    app = Starlette(
        routes=[Route("/health", health)],
        middleware=[Middleware(BearerAuthMiddleware)],
    )

    with TestClient(app) as client:
        response = client.get(
            "/health", headers={"Authorization": f"Bearer {config.mcp_token}"}
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
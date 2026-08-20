import asyncio
import base64

import pytest

from paperless_mcp import server

EXPECTED_TOOLS = {
    "download_document",
    "get_document",
    "list_correspondents",
    "list_document_types",
    "list_tags",
    "search_documents",
    "update_document",
    "upload_document",
}


def test_mcp_exposes_expected_tools():
    tools = asyncio.run(server.mcp.get_tools())

    assert set(tools) == EXPECTED_TOOLS


def test_search_documents_maps_filters_and_reduces_results(monkeypatch):
    captured = {}

    def fake_get(path, params=None):
        captured.update(path=path, params=params)
        return {
            "count": 1,
            "results": [
                {
                    "id": 42,
                    "title": "Invoice",
                    "created": "2026-01-02",
                    "correspondent": 3,
                    "document_type": 4,
                    "tags": [5, 6],
                    "archive_serial_number": 7,
                    "content": "must not leak into search results",
                }
            ],
        }

    monkeypatch.setattr(server, "_get", fake_get)

    result = server.search_documents.fn(
        query="invoice",
        tag_ids=[5, 6],
        correspondent_id=3,
        document_type_id=4,
        created_after="2026-01-01",
        created_before="2026-01-31",
        page_size=10,
    )

    assert captured == {
        "path": "/api/documents/",
        "params": {
            "page_size": 10,
            "ordering": "-created",
            "query": "invoice",
            "tags__id__all": "5,6",
            "correspondent__id": 3,
            "document_type__id": 4,
            "created__date__gte": "2026-01-01",
            "created__date__lte": "2026-01-31",
        },
    }
    assert result == {
        "count": 1,
        "results": [
            {
                "id": 42,
                "title": "Invoice",
                "created": "2026-01-02",
                "correspondent": 3,
                "document_type": 4,
                "tags": [5, 6],
                "archive_serial_number": 7,
            }
        ],
    }


def test_get_document_can_omit_ocr_content(monkeypatch):
    monkeypatch.setattr(
        server,
        "_get",
        lambda path: {
            "id": 42,
            "title": "Invoice",
            "content": "private OCR",
            "tags": [],
        },
    )

    result = server.get_document.fn(document_id=42, include_content=False)

    assert result["id"] == 42
    assert "content" not in result


class FakeResponse:
    def __init__(self, payload=None, *, content=b"", headers=None, error=None):
        self.payload = payload
        self.content = content
        self.headers = headers or {}
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def get(self, path, params=None):
        self.requests.append(("GET", path, params))
        return next(self.responses)

    def post(self, path, data=None, files=None):
        self.requests.append(("POST", path, data, files))
        return next(self.responses)


def test_client_uses_configured_url_and_token(monkeypatch, config):
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(server.httpx, "Client", fake_client)

    server._client()

    assert captured == {
        "base_url": config.paperless_url,
        "headers": {"Authorization": f"Token {config.paperless_token}"},
        "timeout": 30.0,
    }


def test_download_document_returns_encoded_content(monkeypatch):
    client = FakeClient(
        [
            FakeResponse(
                content=b"pdf bytes",
                headers={
                    "content-disposition": 'attachment; filename="invoice.pdf"',
                    "content-type": "application/pdf",
                },
            )
        ]
    )
    monkeypatch.setattr(server, "_client", lambda: client)

    result = server.download_document.fn(document_id=42, original=True)

    assert client.requests == [("GET", "/api/documents/42/download/?original=true", None)]
    assert result == {
        "filename": "invoice.pdf",
        "content_type": "application/pdf",
        "size": 9,
        "content_b64": base64.b64encode(b"pdf bytes").decode("ascii"),
    }


def test_download_document_propagates_http_errors(monkeypatch):
    error = RuntimeError("Paperless request failed")
    client = FakeClient([FakeResponse(error=error)])
    monkeypatch.setattr(server, "_client", lambda: client)

    with pytest.raises(RuntimeError, match="Paperless request failed"):
        server.download_document.fn(document_id=42)


def test_list_tools_follow_absolute_pagination(monkeypatch):
    client = FakeClient(
        [
            FakeResponse(
                {
                    "results": [{"id": 1, "name": "A", "slug": "a", "document_count": 2}],
                    "next": "http://paperless.example.test/api/tags/?page=2",
                }
            ),
            FakeResponse(
                {
                    "results": [{"id": 2, "name": "B", "slug": "b", "document_count": 3}],
                    "next": None,
                }
            ),
        ]
    )
    monkeypatch.setattr(server, "_client", lambda: client)

    result = server.list_tags.fn(page_size=1)

    assert [item["id"] for item in result] == [1, 2]
    assert client.requests == [
        ("GET", "/api/tags/?page_size=1", None),
        ("GET", "http://paperless.example.test/api/tags/?page=2", None),
    ]


def test_update_document_merges_tags(monkeypatch, config):
    monkeypatch.setattr(server, "_get", lambda path: {"tags": [1, 2]})
    captured = {}

    def fake_patch(path, payload):
        captured.update(path=path, payload=payload)
        return {"id": 42, "title": "Updated", "tags": payload["tags"]}

    monkeypatch.setattr(server, "_patch", fake_patch)

    result = server.update_document.fn(
        document_id=42,
        add_tag_ids=[3],
        remove_tag_ids=[1],
    )

    assert captured == {"path": "/api/documents/42/", "payload": {"tags": [2, 3]}}
    assert result["tags"] == [2, 3]


def test_update_document_rejects_conflicting_tag_modes(config):
    with pytest.raises(ValueError, match="mutually exclusive"):
        server.update_document.fn(document_id=42, add_tag_ids=[1], set_tag_ids=[2])


def test_write_tools_are_blocked_in_read_only_mode(config):
    server.CONFIG = server.Config(**{**config.__dict__, "read_only": True})

    with pytest.raises(PermissionError, match="read-only mode"):
        server.update_document.fn(document_id=42, title="Blocked")
    with pytest.raises(PermissionError, match="read-only mode"):
        server.upload_document.fn(filename="blocked.pdf", content_b64="YQ==")


def test_upload_rejects_invalid_base64(config):
    with pytest.raises(ValueError, match="not valid base64"):
        server.upload_document.fn(filename="invalid.pdf", content_b64="not base64")


def test_upload_passes_file_and_metadata(monkeypatch, config):
    client = FakeClient([FakeResponse("task-123")])
    monkeypatch.setattr(server, "_client", lambda: client)
    encoded = base64.b64encode(b"pdf bytes").decode("ascii")

    result = server.upload_document.fn(
        filename="invoice.pdf",
        content_b64=encoded,
        title="Invoice",
        correspondent_id=2,
        document_type_id=3,
        tag_ids=[4, 5],
    )

    method, path, data, files = client.requests[0]
    assert (method, path) == ("POST", "/api/documents/post_document/")
    assert data == {
        "title": "Invoice",
        "correspondent": "2",
        "document_type": "3",
        "tags": ["4", "5"],
    }
    assert files == {"document": ("invoice.pdf", b"pdf bytes")}
    assert result == {"task": "task-123", "filename": "invoice.pdf", "size": 9}
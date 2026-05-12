"""MCP server for Paperless-ngx.

Transport: streamable HTTP (network-exposed, requires bearer token).
Backend:   Paperless-ngx REST API via httpx, authenticated with a
           Paperless API token.

Environment variables:
    PAPERLESS_URL          Base URL of the Paperless instance, e.g. http://192.168.2.23:8000
    PAPERLESS_TOKEN        API token of a Paperless user (Settings -> API tokens)
    PAPERLESS_MCP_TOKEN    Static bearer token clients must present (Authorization: Bearer ...)
    PAPERLESS_MCP_HOST     Bind address (default: 0.0.0.0)
    PAPERLESS_MCP_PORT     Bind port    (default: 8770)
    PAPERLESS_MCP_PATH     HTTP path    (default: /mcp)
    PAPERLESS_READ_ONLY    If "1"/"true", disables update/upload tools.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import uvicorn
from fastmcp import FastMCP
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass(frozen=True)
class Config:
    paperless_url: str
    paperless_token: str
    mcp_token: str
    host: str
    port: int
    path: str
    read_only: bool


def _load_config() -> Config:
    def need(name: str) -> str:
        v = os.environ.get(name, "").strip()
        if not v:
            raise RuntimeError(f"Missing required env var: {name}")
        return v

    return Config(
        paperless_url=need("PAPERLESS_URL").rstrip("/"),
        paperless_token=need("PAPERLESS_TOKEN"),
        mcp_token=need("PAPERLESS_MCP_TOKEN"),
        host=os.environ.get("PAPERLESS_MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("PAPERLESS_MCP_PORT", "8770")),
        path=os.environ.get("PAPERLESS_MCP_PATH", "/mcp"),
        read_only=os.environ.get("PAPERLESS_READ_ONLY", "").lower() in {"1", "true", "yes"},
    )


CONFIG = _load_config()
mcp = FastMCP("paperless-mcp")


# --- auth middleware ------------------------------------------------------

class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject any HTTP request to the MCP endpoint without a valid bearer token."""

    async def dispatch(self, request, call_next):
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or token.strip() != CONFIG.mcp_token:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def _check_writable() -> None:
    if CONFIG.read_only:
        raise PermissionError("Server is in read-only mode (PAPERLESS_READ_ONLY=1).")


# --- paperless client -----------------------------------------------------

def _client() -> httpx.Client:
    return httpx.Client(
        base_url=CONFIG.paperless_url,
        headers={"Authorization": f"Token {CONFIG.paperless_token}"},
        timeout=30.0,
    )


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    with _client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


def _patch(path: str, payload: dict[str, Any]) -> Any:
    with _client() as c:
        r = c.patch(path, json=payload)
        r.raise_for_status()
        return r.json()


# --- tools ----------------------------------------------------------------

@mcp.tool
def search_documents(
    query: Annotated[str, Field(description="Full-text query. Empty string returns most-recent documents.")] = "",
    tag_ids: Annotated[list[int] | None, Field(description="Restrict to documents that have ALL these tag IDs.")] = None,
    correspondent_id: int | None = None,
    document_type_id: int | None = None,
    created_after: Annotated[str | None, Field(description="ISO date YYYY-MM-DD")] = None,
    created_before: Annotated[str | None, Field(description="ISO date YYYY-MM-DD")] = None,
    page_size: Annotated[int, Field(ge=1, le=100)] = 25,
) -> dict:
    """Search Paperless documents. Returns id, title, created, correspondent, tags, type, snippet."""
    params: dict[str, Any] = {"page_size": page_size, "ordering": "-created"}
    if query:
        params["query"] = query
    if tag_ids:
        params["tags__id__all"] = ",".join(str(t) for t in tag_ids)
    if correspondent_id is not None:
        params["correspondent__id"] = correspondent_id
    if document_type_id is not None:
        params["document_type__id"] = document_type_id
    if created_after:
        params["created__date__gte"] = created_after
    if created_before:
        params["created__date__lte"] = created_before

    data = _get("/api/documents/", params=params)
    results = [
        {
            "id": d["id"],
            "title": d.get("title"),
            "created": d.get("created"),
            "correspondent": d.get("correspondent"),
            "document_type": d.get("document_type"),
            "tags": d.get("tags", []),
            "archive_serial_number": d.get("archive_serial_number"),
        }
        for d in data.get("results", [])
    ]
    return {"count": data.get("count", 0), "results": results}


@mcp.tool
def get_document(
    document_id: int,
    include_content: Annotated[bool, Field(description="Include full OCR text in response.")] = True,
) -> dict:
    """Fetch document metadata (and OCR content by default)."""
    d = _get(f"/api/documents/{document_id}/")
    out = {
        "id": d["id"],
        "title": d.get("title"),
        "created": d.get("created"),
        "modified": d.get("modified"),
        "added": d.get("added"),
        "correspondent": d.get("correspondent"),
        "document_type": d.get("document_type"),
        "tags": d.get("tags", []),
        "archive_serial_number": d.get("archive_serial_number"),
        "original_file_name": d.get("original_file_name"),
        "notes": d.get("notes", []),
    }
    if include_content:
        out["content"] = d.get("content", "")
    return out


@mcp.tool
def download_document(
    document_id: int,
    original: Annotated[bool, Field(description="If true, fetch original file; else archived (PDF/A) version.")] = False,
) -> dict:
    """Download a document. Returns base64-encoded bytes plus filename and content type."""
    suffix = "/download/" + ("?original=true" if original else "")
    with _client() as c:
        r = c.get(f"/api/documents/{document_id}{suffix}")
        r.raise_for_status()
        filename = "document"
        cd = r.headers.get("content-disposition", "")
        if "filename=" in cd:
            filename = cd.split("filename=", 1)[1].strip().strip('"')
        return {
            "filename": filename,
            "content_type": r.headers.get("content-type", "application/octet-stream"),
            "size": len(r.content),
            "content_b64": base64.b64encode(r.content).decode("ascii"),
        }


def _list_simple(endpoint: str, page_size: int) -> list[dict]:
    out: list[dict] = []
    next_url: str | None = endpoint + f"?page_size={page_size}"
    with _client() as c:
        while next_url:
            r = c.get(next_url)
            r.raise_for_status()
            data = r.json()
            for item in data.get("results", []):
                out.append({
                    "id": item["id"],
                    "name": item.get("name"),
                    "slug": item.get("slug"),
                    "document_count": item.get("document_count"),
                })
            nxt = data.get("next")
            # next is absolute URL; httpx handles it
            next_url = nxt
    return out


@mcp.tool
def list_tags(page_size: Annotated[int, Field(ge=1, le=500)] = 200) -> list[dict]:
    """List all Paperless tags."""
    return _list_simple("/api/tags/", page_size)


@mcp.tool
def list_correspondents(page_size: Annotated[int, Field(ge=1, le=500)] = 200) -> list[dict]:
    """List all Paperless correspondents."""
    return _list_simple("/api/correspondents/", page_size)


@mcp.tool
def list_document_types(page_size: Annotated[int, Field(ge=1, le=500)] = 200) -> list[dict]:
    """List all Paperless document types."""
    return _list_simple("/api/document_types/", page_size)


@mcp.tool
def update_document(
    document_id: int,
    title: str | None = None,
    correspondent_id: int | None = None,
    document_type_id: int | None = None,
    add_tag_ids: list[int] | None = None,
    remove_tag_ids: list[int] | None = None,
    set_tag_ids: Annotated[list[int] | None, Field(description="If set, REPLACES all tags. Mutually exclusive with add/remove.")] = None,
) -> dict:
    """Update a document's metadata."""
    _check_writable()

    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if correspondent_id is not None:
        payload["correspondent"] = correspondent_id
    if document_type_id is not None:
        payload["document_type"] = document_type_id

    if set_tag_ids is not None:
        if add_tag_ids or remove_tag_ids:
            raise ValueError("set_tag_ids is mutually exclusive with add_tag_ids/remove_tag_ids.")
        payload["tags"] = list(set_tag_ids)
    elif add_tag_ids or remove_tag_ids:
        current = _get(f"/api/documents/{document_id}/").get("tags", [])
        new_tags = set(current)
        if add_tag_ids:
            new_tags.update(add_tag_ids)
        if remove_tag_ids:
            new_tags.difference_update(remove_tag_ids)
        payload["tags"] = sorted(new_tags)

    if not payload:
        raise ValueError("No fields to update.")

    updated = _patch(f"/api/documents/{document_id}/", payload)
    return {
        "id": updated["id"],
        "title": updated.get("title"),
        "tags": updated.get("tags", []),
        "correspondent": updated.get("correspondent"),
        "document_type": updated.get("document_type"),
    }


@mcp.tool
def upload_document(
    filename: Annotated[str, Field(description="Filename including extension, e.g. invoice.pdf")],
    content_b64: Annotated[str, Field(description="Base64-encoded file content.")],
    title: str | None = None,
    correspondent_id: int | None = None,
    document_type_id: int | None = None,
    tag_ids: list[int] | None = None,
) -> dict:
    """Upload a new document to Paperless. Returns the consume task UUID."""
    _check_writable()

    try:
        content = base64.b64decode(content_b64, validate=True)
    except Exception as exc:
        raise ValueError(f"content_b64 is not valid base64: {exc}") from exc

    data: dict[str, Any] = {}
    if title:
        data["title"] = title
    if correspondent_id is not None:
        data["correspondent"] = str(correspondent_id)
    if document_type_id is not None:
        data["document_type"] = str(document_type_id)
    if tag_ids:
        data["tags"] = [str(t) for t in tag_ids]

    files = {"document": (filename, content)}
    with _client() as c:
        r = c.post("/api/documents/post_document/", data=data, files=files)
        r.raise_for_status()
        # Returns a task UUID string (quoted JSON) on success
        try:
            body = r.json()
        except Exception:
            body = r.text
    return {"task": body, "filename": filename, "size": len(content)}


def main() -> None:
    app = mcp.http_app(path=CONFIG.path, middleware=[Middleware(BearerAuthMiddleware)])
    uvicorn.run(app, host=CONFIG.host, port=CONFIG.port, log_level="info")


if __name__ == "__main__":
    main()

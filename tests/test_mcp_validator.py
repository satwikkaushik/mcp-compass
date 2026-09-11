from contextlib import asynccontextmanager

import httpx2
from mcp.shared.exceptions import MCPError

from app.services.mcp_validator import validate_mcp_server


@asynccontextmanager
async def _fake_streams():
    yield (object(), object())


class _FakeSession:
    def __init__(self, *args, error=None, **kwargs):
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def initialize(self):
        if self._error:
            raise self._error

    async def list_tools(self):
        return []


def _patch_transport(monkeypatch, session_error=None):
    monkeypatch.setattr(
        "app.services.mcp_validator.streamable_http_client",
        lambda *a, **kw: _fake_streams(),
    )
    monkeypatch.setattr(
        "app.services.mcp_validator.ClientSession",
        lambda *a, **kw: _FakeSession(error=session_error),
    )


async def test_validate_mcp_server_returns_healthy_on_success(monkeypatch):
    _patch_transport(monkeypatch)
    status = await validate_mcp_server("http://localhost:9000/mcp")
    assert status == "healthy"


async def test_validate_mcp_server_returns_unreachable_on_connect_error(monkeypatch):
    _patch_transport(monkeypatch, session_error=httpx2.ConnectError("refused"))
    status = await validate_mcp_server("http://localhost:9000/mcp")
    assert status == "unreachable"


async def test_validate_mcp_server_returns_unreachable_on_timeout(monkeypatch):
    _patch_transport(monkeypatch, session_error=httpx2.ConnectTimeout("timed out"))
    status = await validate_mcp_server("http://localhost:9000/mcp")
    assert status == "unreachable"


async def test_validate_mcp_server_returns_invalid_on_protocol_error(monkeypatch):
    _patch_transport(
        monkeypatch, session_error=MCPError(code=-32600, message="bad response")
    )
    status = await validate_mcp_server("http://localhost:9000/mcp")
    assert status == "invalid"

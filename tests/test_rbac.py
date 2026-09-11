from unittest.mock import AsyncMock

import pytest

from app.models.server import McpServer
from tests.conftest import auth_headers

FAKE_EMBEDDING = [0.0] * 384


def _server_payload(workspace_id: int, name: str = "srv") -> dict:
    return {
        "name": name,
        "description": "desc",
        "endpoint_url": "http://localhost:9000/mcp",
        "version": "0.1.0",
        "tags": [],
        "workspace_id": workspace_id,
    }


@pytest.fixture
def stub_server_side_effects(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.servers.validate_mcp_server", AsyncMock(return_value="healthy")
    )
    monkeypatch.setattr(
        "app.api.routes.servers.embed_server", lambda *a, **kw: FAKE_EMBEDDING
    )


async def test_member_cannot_publish_server_to_other_workspace(
    client, member_membership, user2, workspace_b, stub_server_side_effects
):
    resp = await client.post(
        "/servers",
        json=_server_payload(workspace_b.id),
        headers=auth_headers(user2.id),
    )
    assert resp.status_code == 403


async def test_non_admin_only_sees_their_own_workspace_servers(
    client, session, user2, member_membership, workspace_a, workspace_b
):
    own_server = McpServer(
        name="own",
        description="d",
        endpoint_url="http://localhost:1/mcp",
        version="0.1.0",
        tags=[],
        workspace_id=workspace_a.id,
    )
    other_server = McpServer(
        name="other",
        description="d",
        endpoint_url="http://localhost:2/mcp",
        version="0.1.0",
        tags=[],
        workspace_id=workspace_b.id,
    )
    session.add_all([own_server, other_server])
    await session.commit()

    resp = await client.get("/servers", headers=auth_headers(user2.id))
    assert resp.status_code == 200
    names = {s["name"] for s in resp.json()}
    assert names == {"own"}


async def test_admin_can_publish_update_and_delete_server(
    client, admin_membership, user1, workspace_a, stub_server_side_effects
):
    create_resp = await client.post(
        "/servers",
        json=_server_payload(workspace_a.id, name="admin-srv"),
        headers=auth_headers(user1.id),
    )
    assert create_resp.status_code == 201
    server_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/servers/{server_id}",
        json={"description": "updated desc"},
        headers=auth_headers(user1.id),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated desc"

    delete_resp = await client.delete(
        f"/servers/{server_id}", headers=auth_headers(user1.id)
    )
    assert delete_resp.status_code == 204

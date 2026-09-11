import jwt

from app.core.config import settings
from tests.conftest import auth_headers


async def test_register_then_login_returns_valid_jwt(client):
    register_resp = await client.post(
        "/auth/register",
        json={"email": "new.user@example.com", "password": "supersecret1"},
    )
    assert register_resp.status_code == 201

    login_resp = await client.post(
        "/auth/login",
        json={"email": "new.user@example.com", "password": "supersecret1"},
    )
    assert login_resp.status_code == 200

    body = login_resp.json()
    assert body["token_type"] == "bearer"
    decoded = jwt.decode(
        body["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    assert "sub" in decoded


async def test_protected_route_without_token_returns_401(client):
    resp = await client.get("/servers")
    assert resp.status_code == 401


async def test_protected_route_with_valid_token_returns_200(client, user1):
    resp = await client.get("/servers", headers=auth_headers(user1.id))
    assert resp.status_code == 200
    assert resp.json() == []

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import check_membership, get_current_user
from app.db.session import get_session
from app.models.server import McpServer, McpServerVersion
from app.models.user import User, WorkspaceMembership
from app.schemas.server import McpServerCreate, McpServerRead, McpServerUpdate
from app.services.mcp_validator import validate_mcp_server

router = APIRouter(prefix="/servers", tags=["servers"])


def _snapshot_version(server: McpServer) -> McpServerVersion:
    return McpServerVersion(
        server_id=server.id,
        version=server.version,
        name=server.name,
        description=server.description,
        endpoint_url=server.endpoint_url,
        tags=server.tags,
    )


@router.post(
    "",
    response_model=McpServerRead,
    status_code=201,
    summary="Publish a server",
    description="Registers a new MCP server and records its initial version snapshot.",
)
async def publish_server(
    payload: McpServerCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await check_membership(current_user, payload.workspace_id, session)

    server = McpServer(**payload.model_dump())
    session.add(server)
    await session.flush()

    server.connectivity_status = await validate_mcp_server(server.endpoint_url)
    server.last_checked_at = datetime.now(UTC)

    session.add(_snapshot_version(server))
    await session.commit()
    await session.refresh(server)
    return server


@router.get(
    "",
    response_model=list[McpServerRead],
    summary="Discover servers",
    description="Lists registered servers in the caller's workspaces, optionally filtered by tag.",
)
async def discover_servers(
    tag: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    member_workspaces = select(WorkspaceMembership.workspace_id).where(
        WorkspaceMembership.user_id == current_user.id
    )
    stmt = select(McpServer).where(McpServer.workspace_id.in_(member_workspaces))
    if tag:
        stmt = stmt.where(McpServer.tags.any(tag))
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{server_id}",
    response_model=McpServerRead,
    summary="Get a server",
    description="Fetches a single server by its ID.",
)
async def get_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    server = await session.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    await check_membership(current_user, server.workspace_id, session)
    return server


@router.patch(
    "/{server_id}",
    response_model=McpServerRead,
    summary="Update a server",
    description="Updates a server's fields and records a new version snapshot.",
)
async def update_server(
    server_id: int,
    payload: McpServerUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    server = await session.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    await check_membership(current_user, server.workspace_id, session)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(server, field, value)
    server.updated_at = datetime.now(UTC)

    server.connectivity_status = await validate_mcp_server(server.endpoint_url)
    server.last_checked_at = datetime.now(UTC)

    session.add(server)
    await session.flush()

    session.add(_snapshot_version(server))
    await session.commit()
    await session.refresh(server)
    return server


@router.delete(
    "/{server_id}",
    status_code=204,
    summary="Delete a server",
    description="Deletes a server and its version history.",
)
async def delete_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    server = await session.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    await check_membership(
        current_user, server.workspace_id, session, required_role="admin"
    )
    await session.delete(server)
    await session.commit()

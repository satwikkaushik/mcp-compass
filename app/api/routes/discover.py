from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.server import McpServer
from app.models.user import User, WorkspaceMembership
from app.schemas.discover import DiscoverRequest, DiscoverResponse
from app.services.embeddings import embed_text
from app.services.rag import generate_discovery_answer

router = APIRouter(prefix="/discover", tags=["discover"])

TOP_K = 3


@router.post(
    "",
    response_model=DiscoverResponse,
    summary="Natural-language server discovery",
    description="Embeds the query, retrieves the closest servers by cosine distance, and generates a grounded explanation.",
)
async def discover(
    payload: DiscoverRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query_embedding = embed_text(payload.query)

    member_workspaces = select(WorkspaceMembership.workspace_id).where(
        WorkspaceMembership.user_id == current_user.id
    )

    stmt = (
        select(McpServer)
        .where(
            McpServer.workspace_id.in_(member_workspaces),
            McpServer.embedding.is_not(None),
        )
        .order_by(McpServer.embedding.cosine_distance(query_embedding))
        .limit(TOP_K)
    )
    result = await session.execute(stmt)
    matches = result.scalars().all()

    answer = generate_discovery_answer(payload.query, matches)

    return DiscoverResponse(answer=answer, matches=matches)

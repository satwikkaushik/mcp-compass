import jwt
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User, WorkspaceMembership

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        paylaod = decode_access_token(token)
        user_id = int(paylaod["sub"])
    except jwt.PyJWTError, KeyError, ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )

    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Token")

    return user


async def check_membership(
    user: User,
    workspace_id: int,
    session: AsyncSession,
    required_role: str | None = None,
) -> WorkspaceMembership:
    stmt = select(WorkspaceMembership).where(
        WorkspaceMembership.user_id == user.id,
        WorkspaceMembership.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    membership = result.scalar_one_or_none()
    if not membership or (required_role and membership.role != required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return membership

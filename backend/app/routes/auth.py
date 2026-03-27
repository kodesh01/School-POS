from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    res = await db.execute(select(User).where(User.username == payload.username))
    user = res.scalar_one_or_none()
    if not user or not user.is_active or verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    role = (await db.execute(select(Role).where(Role.id == user.role_id))).scalar_one()
    return TokenPair(
        access_token=create_access_token(user.username, role.name),
        refresh_token=create_refresh_token(user.username, role.name),
    )


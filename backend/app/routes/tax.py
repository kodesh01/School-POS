from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.pos import TaxProfile
from app.schemas.common import Page, PageMeta
from app.schemas.pos import TaxProfileIn, TaxProfileOut

router = APIRouter(prefix="/tax", tags=["tax"])


@router.get("/profiles", response_model=Page[TaxProfileOut], dependencies=[Depends(require_roles("Admin", "Staff", "Accountant"))])
async def list_tax_profiles(
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    is_active: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[TaxProfileOut]:
    stmt = select(TaxProfile).order_by(TaxProfile.created_at.desc())
    if q:
        stmt = stmt.where(TaxProfile.name.ilike(f"%{q}%"))
    if is_active is not None:
        stmt = stmt.where(TaxProfile.is_active == is_active)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    items = list((await db.execute(stmt.limit(limit).offset(offset))).scalars().all())
    return Page(items=items, meta=PageMeta(total=total, limit=limit, offset=offset))


@router.post("/profiles", response_model=TaxProfileOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("Admin"))])
async def create_tax_profile(payload: TaxProfileIn, db: AsyncSession = Depends(get_db)) -> TaxProfileOut:
    existing = (await db.execute(select(TaxProfile).where(TaxProfile.name == payload.name))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Tax profile already exists")
    tp = TaxProfile(**payload.model_dump())
    db.add(tp)
    await db.commit()
    await db.refresh(tp)
    return tp


@router.put("/profiles/{tax_profile_id}", response_model=TaxProfileOut, dependencies=[Depends(require_roles("Admin"))])
async def update_tax_profile(tax_profile_id: str, payload: TaxProfileIn, db: AsyncSession = Depends(get_db)) -> TaxProfileOut:
    tp = (await db.execute(select(TaxProfile).where(TaxProfile.id == tax_profile_id))).scalar_one_or_none()
    if not tp:
        raise HTTPException(status_code=404, detail="Tax profile not found")
    for k, v in payload.model_dump().items():
        setattr(tp, k, v)
    await db.commit()
    await db.refresh(tp)
    return tp


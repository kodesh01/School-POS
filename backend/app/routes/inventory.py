from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.inventory import Product, StockMovement, Supplier
from app.schemas.common import Page, PageMeta
from app.schemas.inventory import ProductIn, ProductOut, StockMovementIn, StockMovementOut, SupplierIn, SupplierOut
from app.services.ws import hub

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/suppliers", response_model=Page[SupplierOut], dependencies=[Depends(require_roles("Admin", "Staff"))])
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[SupplierOut]:
    stmt = select(Supplier).order_by(Supplier.created_at.desc())
    if q:
        stmt = stmt.where(Supplier.name.ilike(f"%{q}%"))
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    items = list((await db.execute(stmt.limit(limit).offset(offset))).scalars().all())
    return Page(items=items, meta=PageMeta(total=total, limit=limit, offset=offset))


@router.post("/suppliers", response_model=SupplierOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("Admin"))])
async def create_supplier(payload: SupplierIn, db: AsyncSession = Depends(get_db)) -> SupplierOut:
    existing = (await db.execute(select(Supplier).where(Supplier.name == payload.name))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Supplier already exists")
    s = Supplier(**payload.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.get("/products", response_model=Page[ProductOut], dependencies=[Depends(require_roles("Admin", "Staff", "Accountant"))])
async def list_products(
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    category: str | None = None,
    low_stock: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[ProductOut]:
    stmt = select(Product).order_by(Product.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Product.name.ilike(like)) | (Product.sku.ilike(like)) | (Product.barcode.ilike(like)))
    if category:
        stmt = stmt.where(Product.category == category)
    if low_stock:
        stmt = stmt.where(Product.stock_on_hand <= Product.reorder_level)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    items = list((await db.execute(stmt.limit(limit).offset(offset))).scalars().all())
    return Page(items=items, meta=PageMeta(total=total, limit=limit, offset=offset))


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("Admin", "Staff"))])
async def create_product(payload: ProductIn, db: AsyncSession = Depends(get_db)) -> ProductOut:
    existing = (await db.execute(select(Product).where(Product.sku == payload.sku))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="SKU already exists")
    p = Product(**payload.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.put("/products/{product_id}", response_model=ProductOut, dependencies=[Depends(require_roles("Admin", "Staff"))])
async def update_product(product_id: str, payload: ProductIn, db: AsyncSession = Depends(get_db)) -> ProductOut:
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in payload.model_dump().items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p


@router.post("/stock/move", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("Admin", "Staff"))])
async def move_stock(payload: StockMovementIn, db: AsyncSession = Depends(get_db)) -> StockMovementOut:
    p = (await db.execute(select(Product).where(Product.id == str(payload.product_id)))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    qty = payload.quantity
    if payload.movement_type == "in":
        p.stock_on_hand += qty
    elif payload.movement_type == "out":
        if p.stock_on_hand < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        p.stock_on_hand -= qty
    elif payload.movement_type == "adjust":
        p.stock_on_hand = qty
    else:
        raise HTTPException(status_code=400, detail="Invalid movement_type")

    m = StockMovement(**payload.model_dump())
    db.add(m)
    await db.commit()
    await db.refresh(m)

    await hub.broadcast("stock.updated", {"product_id": str(p.id), "stock_on_hand": p.stock_on_hand})
    return m


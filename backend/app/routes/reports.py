from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.inventory import Product
from app.models.pos import Invoice, InvoiceItem
from app.models.student import StudentFeePayment

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales/summary", dependencies=[Depends(require_roles("Admin", "Accountant"))])
async def sales_summary(
    db: AsyncSession = Depends(get_db),
    start: dt.date | None = Query(None),
    end: dt.date | None = Query(None),
) -> dict:
    stmt = select(
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.grand_total), 0),
        func.coalesce(func.sum(Invoice.tax_total), 0),
    )
    if start:
        stmt = stmt.where(Invoice.billed_at >= dt.datetime.combine(start, dt.time.min))
    if end:
        stmt = stmt.where(Invoice.billed_at <= dt.datetime.combine(end, dt.time.max))
    count, total, tax = (await db.execute(stmt)).one()
    return {"invoices": int(count), "sales_total": float(total), "tax_total": float(tax)}


@router.get("/fees/summary", dependencies=[Depends(require_roles("Admin", "Accountant"))])
async def fee_summary(
    db: AsyncSession = Depends(get_db),
    start: dt.date | None = Query(None),
    end: dt.date | None = Query(None),
) -> dict:
    stmt = select(func.count(StudentFeePayment.id), func.coalesce(func.sum(StudentFeePayment.amount), 0))
    if start:
        stmt = stmt.where(StudentFeePayment.paid_at >= dt.datetime.combine(start, dt.time.min))
    if end:
        stmt = stmt.where(StudentFeePayment.paid_at <= dt.datetime.combine(end, dt.time.max))
    count, total = (await db.execute(stmt)).one()
    return {"receipts": int(count), "fee_total": float(total)}


@router.get("/inventory/low-stock", dependencies=[Depends(require_roles("Admin", "Staff"))])
async def low_stock(db: AsyncSession = Depends(get_db), limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    res = await db.execute(
        select(Product).where(Product.stock_on_hand <= Product.reorder_level).order_by(Product.stock_on_hand.asc()).limit(limit)
    )
    return [
        {"id": str(p.id), "sku": p.sku, "name": p.name, "stock_on_hand": p.stock_on_hand, "reorder_level": p.reorder_level}
        for p in res.scalars().all()
    ]


@router.get("/analytics/most-sold", dependencies=[Depends(require_roles("Admin", "Accountant"))])
async def most_sold(
    db: AsyncSession = Depends(get_db),
    start: dt.date | None = Query(None),
    end: dt.date | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    stmt = (
        select(InvoiceItem.sku, InvoiceItem.name, func.sum(InvoiceItem.quantity).label("qty"))
        .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
        .group_by(InvoiceItem.sku, InvoiceItem.name)
        .order_by(func.sum(InvoiceItem.quantity).desc())
        .limit(limit)
    )
    if start:
        stmt = stmt.where(Invoice.billed_at >= dt.datetime.combine(start, dt.time.min))
    if end:
        stmt = stmt.where(Invoice.billed_at <= dt.datetime.combine(end, dt.time.max))
    rows = (await db.execute(stmt)).all()
    return [{"sku": sku, "name": name, "quantity": int(qty)} for sku, name, qty in rows]


@router.get("/analytics/peak-hours", dependencies=[Depends(require_roles("Admin", "Accountant"))])
async def peak_hours(db: AsyncSession = Depends(get_db), days: int = Query(30, ge=1, le=365)) -> list[dict]:
    since = dt.datetime.utcnow() - dt.timedelta(days=days)
    hour_part = text("hour")
    stmt = (
        select(func.datepart(hour_part, Invoice.billed_at).label("hour"), func.count(Invoice.id).label("count"))
        .where(Invoice.billed_at >= since)
        .group_by(func.datepart(hour_part, Invoice.billed_at))
        .order_by(func.count(Invoice.id).desc())
    )
    rows = (await db.execute(stmt)).all()
    return [{"hour": int(h), "count": int(c)} for h, c in rows]


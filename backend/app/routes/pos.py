from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.inventory import Product, StockMovement
from app.models.pos import Invoice, InvoiceItem, Payment, TaxProfile
from app.schemas.pos import InvoiceCreate, InvoiceOut
from app.services.pos_calc import exclusive_base_from_inclusive, money, split_gst
from app.services.ws import hub

router = APIRouter(prefix="/pos", tags=["pos"])


def _next_invoice_no() -> str:
    return "INV-" + dt.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


@router.post(
    "/invoices",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("Admin", "Staff", "Accountant"))],
)
async def create_invoice(payload: InvoiceCreate, db: AsyncSession = Depends(get_db)) -> InvoiceOut:
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items")
    if not payload.payments:
        raise HTTPException(status_code=400, detail="No payments")

    invoice = Invoice(
        invoice_no=_next_invoice_no(),
        student_id=payload.student_id,
        subtotal=0,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        discount_amount=0,
        tax_total=0,
        cgst_total=0,
        sgst_total=0,
        grand_total=0,
    )

    subtotal = money(0)
    cgst_total = money(0)
    sgst_total = money(0)

    for it in payload.items:
        prod = (await db.execute(select(Product).where(Product.id == str(it.product_id)))).scalar_one_or_none()
        if not prod or not prod.is_active:
            raise HTTPException(status_code=404, detail=f"Product not found: {it.product_id}")
        if prod.stock_on_hand < it.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {prod.sku}")

        cgst_rate = money(0)
        sgst_rate = money(0)
        if prod.tax_profile_id:
            tp = (await db.execute(select(TaxProfile).where(TaxProfile.id == str(prod.tax_profile_id)))).scalar_one_or_none()
            if tp and tp.is_active:
                cgst_rate = money(tp.cgst_rate)
                sgst_rate = money(tp.sgst_rate)

        unit_price = money(prod.selling_price)
        line_total_input = unit_price * money(it.quantity)
        line_base = (
            exclusive_base_from_inclusive(line_total_input, cgst_rate, sgst_rate) if prod.is_tax_inclusive else line_total_input
        )

        taxes = split_gst(line_base, cgst_rate, sgst_rate)
        line_total = (line_base + taxes.total_tax).quantize(money(0))

        invoice.items.append(
            InvoiceItem(
                product_id=prod.id,
                sku=prod.sku,
                name=prod.name,
                quantity=it.quantity,
                unit_price=float(unit_price),
                line_subtotal=float(line_base),
                tax_profile_id=prod.tax_profile_id,
                cgst_rate=float(cgst_rate),
                sgst_rate=float(sgst_rate),
                cgst_amount=float(taxes.cgst_amount),
                sgst_amount=float(taxes.sgst_amount),
                line_total=float(line_total),
            )
        )

        subtotal += line_base
        cgst_total += taxes.cgst_amount
        sgst_total += taxes.sgst_amount

        prod.stock_on_hand -= it.quantity
        db.add(StockMovement(product_id=prod.id, movement_type="out", quantity=it.quantity, reason=f"Sale {invoice.invoice_no}"))

    discount_amount = money(0)
    if payload.discount_type == "percent":
        discount_amount = (subtotal * money(payload.discount_value) / money(100)).quantize(money(0))
    elif payload.discount_type == "flat":
        discount_amount = money(payload.discount_value)

    discounted_subtotal = (subtotal - discount_amount).quantize(money(0))
    if discounted_subtotal < 0:
        raise HTTPException(status_code=400, detail="Discount exceeds subtotal")

    tax_total = (cgst_total + sgst_total).quantize(money(0))
    grand_total = (discounted_subtotal + tax_total).quantize(money(0))

    payment_amounts = [money(p.amount) for p in payload.payments]
    paid_amount = sum(payment_amounts, money(0))
    delta = (grand_total - paid_amount).quantize(money(0))
    tolerance = money("0.01")
    if abs(delta) > tolerance:
        raise HTTPException(
            status_code=400,
            detail=f"Payments must equal grand_total (expected {float(grand_total):.2f}, got {float(paid_amount):.2f})",
        )
    # Accept tiny rounding mismatch and normalize final payment.
    if delta != money(0):
        payment_amounts[-1] = (payment_amounts[-1] + delta).quantize(money(0))

    invoice.subtotal = float(subtotal)
    invoice.discount_amount = float(discount_amount)
    invoice.cgst_total = float(cgst_total)
    invoice.sgst_total = float(sgst_total)
    invoice.tax_total = float(tax_total)
    invoice.grand_total = float(grand_total)

    for i, p in enumerate(payload.payments):
        invoice.payments.append(Payment(mode=p.mode, amount=float(payment_amounts[i]), reference=p.reference))

    db.add(invoice)
    await db.commit()
    res = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice.id)
        .options(selectinload(Invoice.items), selectinload(Invoice.payments))
    )
    created = res.scalar_one()

    await hub.broadcast(
        "sale.created",
        {"invoice_id": str(created.id), "invoice_no": created.invoice_no, "grand_total": created.grand_total},
    )
    return created


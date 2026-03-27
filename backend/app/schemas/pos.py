from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class TaxProfileIn(BaseModel):
    name: str
    cgst_rate: float = 0
    sgst_rate: float = 0
    is_active: bool = True


class TaxProfileOut(TaxProfileIn, Timestamped):
    pass


class InvoiceItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class PaymentCreate(BaseModel):
    mode: str
    amount: float
    reference: str | None = None


class InvoiceCreate(BaseModel):
    student_id: uuid.UUID | None = None
    items: list[InvoiceItemCreate]
    discount_type: str | None = None  # percent/flat
    discount_value: float = 0
    payments: list[PaymentCreate]


class InvoiceItemOut(Timestamped):
    invoice_id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    name: str
    quantity: int
    unit_price: float
    line_subtotal: float
    cgst_rate: float
    sgst_rate: float
    cgst_amount: float
    sgst_amount: float
    line_total: float


class PaymentOut(Timestamped):
    invoice_id: uuid.UUID
    mode: str
    amount: float
    reference: str | None
    paid_at: dt.datetime


class InvoiceOut(Timestamped):
    invoice_no: str
    student_id: uuid.UUID | None
    subtotal: float
    discount_type: str | None
    discount_value: float
    discount_amount: float
    tax_total: float
    cgst_total: float
    sgst_total: float
    grand_total: float
    payment_status: str
    billed_at: dt.datetime
    items: list[InvoiceItemOut]
    payments: list[PaymentOut]


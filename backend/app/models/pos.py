from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TaxProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tax_profiles"

    name: Mapped[str] = mapped_column(sa.String(80), nullable=False, unique=True, index=True)
    cgst_rate: Mapped[float] = mapped_column(sa.Numeric(5, 2), nullable=False, server_default=sa.text("0"))
    sgst_rate: Mapped[float] = mapped_column(sa.Numeric(5, 2), nullable=False, server_default=sa.text("0"))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("1"))

    __table_args__ = (sa.Index("ix_tax_profiles_active", "is_active"),)


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoices"

    invoice_no: Mapped[str] = mapped_column(sa.String(40), nullable=False, unique=True, index=True)
    student_id: Mapped[sa.Uuid | None] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("students.id"), nullable=True, index=True)

    subtotal: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    discount_type: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    discount_value: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    discount_amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))

    tax_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    cgst_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    sgst_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    grand_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)

    payment_status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default=sa.text("'paid'"))
    billed_at: Mapped[dt.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.sysutcdatetime())

    items: Mapped[list["InvoiceItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        sa.Index("ix_invoices_billed_at", "billed_at"),
        sa.Index("ix_invoices_student_billed", "student_id", "billed_at"),
    )


class InvoiceItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False, index=True)
    product_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("products.id"), nullable=False, index=True)

    sku: Mapped[str] = mapped_column(sa.String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(160), nullable=False)
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    unit_price: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    line_subtotal: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)

    tax_profile_id: Mapped[sa.Uuid | None] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("tax_profiles.id"), nullable=True, index=True)
    cgst_rate: Mapped[float] = mapped_column(sa.Numeric(5, 2), nullable=False, server_default=sa.text("0"))
    sgst_rate: Mapped[float] = mapped_column(sa.Numeric(5, 2), nullable=False, server_default=sa.text("0"))
    cgst_amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    sgst_amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False, server_default=sa.text("0"))
    line_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)

    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    __table_args__ = (sa.Index("ix_invoice_items_invoice_product", "invoice_id", "product_id"),)


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"

    invoice_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(sa.String(20), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(sa.String(80), nullable=True, index=True)
    paid_at: Mapped[dt.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.sysutcdatetime())

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    __table_args__ = (sa.Index("ix_payments_mode_paid_at", "mode", "paid_at"),)


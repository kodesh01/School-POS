from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(sa.String(120), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(sa.String(30), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="supplier")


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    barcode: Mapped[str | None] = mapped_column(sa.String(50), nullable=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(sa.String(160), nullable=False, index=True)
    category: Mapped[str] = mapped_column(sa.String(40), nullable=False, index=True)  # books/uniforms/stationery

    supplier_id: Mapped[sa.Uuid | None] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("suppliers.id"), nullable=True, index=True)
    supplier: Mapped["Supplier | None"] = relationship(back_populates="products")

    cost_price: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    selling_price: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    is_tax_inclusive: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("0"))

    tax_profile_id: Mapped[sa.Uuid | None] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("tax_profiles.id"), nullable=True, index=True)

    stock_on_hand: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    reorder_level: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("5"))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("1"))

    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")

    __table_args__ = (
        sa.Index("ix_products_category_active", "category", "is_active"),
        sa.Index("ix_products_low_stock", "stock_on_hand", "reorder_level"),
    )


class StockMovement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "stock_movements"

    product_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("products.id"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(sa.String(20), nullable=False, index=True)  # in/out/adjust
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    moved_at: Mapped[dt.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.sysutcdatetime())

    product: Mapped["Product"] = relationship(back_populates="stock_movements")

    __table_args__ = (sa.Index("ix_stock_product_moved", "product_id", "moved_at"),)


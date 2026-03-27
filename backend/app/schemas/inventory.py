from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel

from app.schemas.common import Timestamped


class SupplierIn(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class SupplierOut(SupplierIn, Timestamped):
    pass


class ProductIn(BaseModel):
    sku: str
    barcode: str | None = None
    name: str
    category: str
    supplier_id: uuid.UUID | None = None
    cost_price: float
    selling_price: float
    is_tax_inclusive: bool = False
    tax_profile_id: uuid.UUID | None = None
    stock_on_hand: int = 0
    reorder_level: int = 5
    is_active: bool = True


class ProductOut(ProductIn, Timestamped):
    pass


class StockMovementIn(BaseModel):
    product_id: uuid.UUID
    movement_type: str
    quantity: int
    reason: str | None = None


class StockMovementOut(StockMovementIn, Timestamped):
    moved_at: dt.datetime


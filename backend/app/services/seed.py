from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.inventory import Product, Supplier
from app.models.pos import TaxProfile
from app.models.user import Role, User

logger = logging.getLogger(__name__)


async def seed_if_empty(db: AsyncSession) -> None:
    async def one_or_none(stmt):
        # Fully materialize rows to avoid pending cursor state with aioodbc/pyodbc.
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return rows[0] if rows else None

    roles = ["Admin", "Staff", "Accountant"]
    existing_roles = await db.execute(select(Role))
    existing_role_names = {r.name for r in existing_roles.scalars().all()}
    for r in roles:
        if r not in existing_role_names:
            db.add(Role(name=r, description=f"{r} role"))
    await db.flush()

    admin = await one_or_none(select(User).where(User.username == "admin"))
    if not admin:
        admin_role = await one_or_none(select(Role).where(Role.name == "Admin"))
        if not admin_role:
            raise RuntimeError("Admin role not found during seed")
        db.add(
            User(
                username="admin",
                full_name="System Administrator",
                hashed_password=hash_password("Admin@123"),
                role_id=admin_role.id,
                is_active=True,
            )
        )
        logger.info("Seeded default admin user: admin / Admin@123")

    gst5 = await one_or_none(select(TaxProfile).where(TaxProfile.name == "GST 5%"))
    if not gst5:
        db.add(TaxProfile(name="GST 5%", cgst_rate=2.5, sgst_rate=2.5, is_active=True))
    gst12 = await one_or_none(select(TaxProfile).where(TaxProfile.name == "GST 12%"))
    if not gst12:
        db.add(TaxProfile(name="GST 12%", cgst_rate=6, sgst_rate=6, is_active=True))
    await db.flush()

    any_product = await one_or_none(select(Product).limit(1))
    if not any_product:
        supplier = await one_or_none(select(Supplier).where(Supplier.name == "Default Supplier"))
        if not supplier:
            supplier = Supplier(name="Default Supplier", phone="9999999999")
            db.add(supplier)
            await db.flush()

        tp = await one_or_none(select(TaxProfile).where(TaxProfile.name == "GST 5%"))
        if not tp:
            raise RuntimeError("GST 5% tax profile not found during seed")
        db.add_all(
            [
                Product(
                    sku="BK-ENG-001",
                    barcode="890000000001",
                    name="English Textbook Grade 5",
                    category="books",
                    supplier_id=supplier.id,
                    cost_price=120,
                    selling_price=150,
                    is_tax_inclusive=False,
                    tax_profile_id=tp.id,
                    stock_on_hand=50,
                    reorder_level=10,
                ),
                Product(
                    sku="UN-SHIRT-M",
                    barcode="890000000002",
                    name="School Uniform Shirt (M)",
                    category="uniforms",
                    supplier_id=supplier.id,
                    cost_price=180,
                    selling_price=250,
                    is_tax_inclusive=True,
                    tax_profile_id=tp.id,
                    stock_on_hand=30,
                    reorder_level=5,
                ),
                Product(
                    sku="ST-PEN-BLU",
                    barcode="890000000003",
                    name="Blue Ball Pen",
                    category="stationery",
                    supplier_id=supplier.id,
                    cost_price=5,
                    selling_price=10,
                    is_tax_inclusive=False,
                    tax_profile_id=tp.id,
                    stock_on_hand=200,
                    reorder_level=50,
                ),
            ]
        )
        logger.info("Seeded sample products.")

    await db.commit()


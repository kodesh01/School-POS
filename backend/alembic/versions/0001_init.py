"""Initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-03-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # (Same as before; kept in one migration for easy setup.)
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("role_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)
    op.create_index("ix_users_role_active", "users", ["role_id", "is_active"], unique=False)

    op.create_table(
        "students",
        sa.Column("student_code", sa.String(length=30), nullable=False),
        sa.Column("first_name", sa.String(length=60), nullable=False),
        sa.Column("last_name", sa.String(length=60), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("class_name", sa.String(length=40), nullable=False),
        sa.Column("section", sa.String(length=10), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_student_code", "students", ["student_code"], unique=True)
    op.create_index("ix_students_class_name", "students", ["class_name"], unique=False)
    op.create_index("ix_students_section", "students", ["section"], unique=False)
    op.create_index("ix_students_class_section", "students", ["class_name", "section"], unique=False)

    op.create_table(
        "parent_contacts",
        sa.Column("student_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("relation", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parent_contacts_student_id", "parent_contacts", ["student_id"], unique=False)
    op.create_index("ix_parent_contacts_phone", "parent_contacts", ["phone"], unique=False)

    op.create_table(
        "student_fee_payments",
        sa.Column("student_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("receipt_no", sa.String(length=40), nullable=False),
        sa.Column("period", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_mode", sa.String(length=20), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_fee_payments_student_id", "student_fee_payments", ["student_id"], unique=False)
    op.create_index("ix_student_fee_payments_receipt_no", "student_fee_payments", ["receipt_no"], unique=True)
    op.create_index("ix_student_fee_payments_period", "student_fee_payments", ["period"], unique=False)
    op.create_index("ix_fee_student_period", "student_fee_payments", ["student_id", "period"], unique=False)

    op.create_table(
        "suppliers",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suppliers_name", "suppliers", ["name"], unique=True)
    op.create_index("ix_suppliers_phone", "suppliers", ["phone"], unique=False)

    op.create_table(
        "tax_profiles",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("cgst_rate", sa.Numeric(precision=5, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("sgst_rate", sa.Numeric(precision=5, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tax_profiles_name", "tax_profiles", ["name"], unique=True)
    op.create_index("ix_tax_profiles_active", "tax_profiles", ["is_active"], unique=False)

    op.create_table(
        "products",
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("supplier_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("cost_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("selling_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_tax_inclusive", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("tax_profile_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("stock_on_hand", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reorder_level", sa.Integer(), server_default=sa.text("5"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["tax_profile_id"], ["tax_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_barcode", "products", ["barcode"], unique=True)
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_category", "products", ["category"], unique=False)
    op.create_index("ix_products_supplier_id", "products", ["supplier_id"], unique=False)
    op.create_index("ix_products_tax_profile_id", "products", ["tax_profile_id"], unique=False)
    op.create_index("ix_products_category_active", "products", ["category", "is_active"], unique=False)
    op.create_index("ix_products_low_stock", "products", ["stock_on_hand", "reorder_level"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("product_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=True),
        sa.Column("moved_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"], unique=False)
    op.create_index("ix_stock_movements_movement_type", "stock_movements", ["movement_type"], unique=False)
    op.create_index("ix_stock_product_moved", "stock_movements", ["product_id", "moved_at"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("invoice_no", sa.String(length=40), nullable=False),
        sa.Column("student_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_type", sa.String(length=10), nullable=True),
        sa.Column("discount_value", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("tax_total", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("cgst_total", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("sgst_total", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("grand_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_status", sa.String(length=20), server_default=sa.text("'paid'"), nullable=False),
        sa.Column("billed_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_invoice_no", "invoices", ["invoice_no"], unique=True)
    op.create_index("ix_invoices_student_id", "invoices", ["student_id"], unique=False)
    op.create_index("ix_invoices_billed_at", "invoices", ["billed_at"], unique=False)
    op.create_index("ix_invoices_student_billed", "invoices", ["student_id", "billed_at"], unique=False)

    op.create_table(
        "invoice_items",
        sa.Column("invoice_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("product_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("line_subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("tax_profile_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("cgst_rate", sa.Numeric(precision=5, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("sgst_rate", sa.Numeric(precision=5, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("sgst_amount", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["tax_profile_id"], ["tax_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"], unique=False)
    op.create_index("ix_invoice_items_product_id", "invoice_items", ["product_id"], unique=False)
    op.create_index("ix_invoice_items_sku", "invoice_items", ["sku"], unique=False)
    op.create_index("ix_invoice_items_tax_profile_id", "invoice_items", ["tax_profile_id"], unique=False)
    op.create_index("ix_invoice_items_invoice_product", "invoice_items", ["invoice_id", "product_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("invoice_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("reference", sa.String(length=80), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"], unique=False)
    op.create_index("ix_payments_mode", "payments", ["mode"], unique=False)
    op.create_index("ix_payments_reference", "payments", ["reference"], unique=False)
    op.create_index("ix_payments_mode_paid_at", "payments", ["mode", "paid_at"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=60), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("sysutcdatetime()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"], unique=False)
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"], unique=False)
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_audit_actor_occurred", "audit_logs", ["actor_user_id", "occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("stock_movements")
    op.drop_table("products")
    op.drop_table("tax_profiles")
    op.drop_table("suppliers")
    op.drop_table("student_fee_payments")
    op.drop_table("parent_contacts")
    op.drop_table("students")
    op.drop_table("users")
    op.drop_table("roles")

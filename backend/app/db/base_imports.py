"""
Central import point for SQLAlchemy models so Alembic can discover them.
"""

from app.models.audit_log import AuditLog  # noqa: F401
from app.models.inventory import Product, StockMovement, Supplier  # noqa: F401
from app.models.pos import Invoice, InvoiceItem, Payment, TaxProfile  # noqa: F401
from app.models.student import ParentContact, Student, StudentFeePayment  # noqa: F401
from app.models.user import Role, User  # noqa: F401


from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[sa.Uuid | None] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(sa.String(60), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(sa.String(60), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True, index=True)
    message: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    occurred_at: Mapped[dt.datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.sysutcdatetime(), index=True
    )

    __table_args__ = (
        sa.Index("ix_audit_entity", "entity_type", "entity_id"),
        sa.Index("ix_audit_actor_occurred", "actor_user_id", "occurred_at"),
    )


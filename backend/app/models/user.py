from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(sa.String(50), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(sa.String(80), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("1"))

    role_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False, index=True)
    role: Mapped["Role"] = relationship(back_populates="users")

    __table_args__ = (sa.Index("ix_users_role_active", "role_id", "is_active"),)


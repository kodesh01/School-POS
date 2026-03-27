from __future__ import annotations

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Student(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "students"

    student_code: Mapped[str] = mapped_column(sa.String(30), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(sa.String(60), nullable=False)
    last_name: Mapped[str | None] = mapped_column(sa.String(60), nullable=True)
    date_of_birth: Mapped[dt.date | None] = mapped_column(sa.Date, nullable=True)

    class_name: Mapped[str] = mapped_column(sa.String(40), nullable=False, index=True)
    section: Mapped[str | None] = mapped_column(sa.String(10), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("1"))

    parents: Mapped[list["ParentContact"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    fee_payments: Mapped[list["StudentFeePayment"]] = relationship(back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (sa.Index("ix_students_class_section", "class_name", "section"),)


class ParentContact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "parent_contacts"

    student_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("students.id"), nullable=False, index=True)
    relation: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(sa.String(30), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)

    student: Mapped["Student"] = relationship(back_populates="parents")


class StudentFeePayment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_fee_payments"

    student_id: Mapped[sa.Uuid] = mapped_column(sa.Uuid(as_uuid=True), sa.ForeignKey("students.id"), nullable=False, index=True)
    receipt_no: Mapped[str] = mapped_column(sa.String(40), nullable=False, unique=True, index=True)
    period: Mapped[str] = mapped_column(sa.String(40), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    paid_at: Mapped[dt.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.sysutcdatetime())

    student: Mapped["Student"] = relationship(back_populates="fee_payments")

    __table_args__ = (sa.Index("ix_fee_student_period", "student_id", "period"),)


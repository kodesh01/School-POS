from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field

from app.schemas.common import Timestamped


class ParentContactIn(BaseModel):
    relation: str
    name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class ParentContactOut(ParentContactIn, Timestamped):
    student_id: uuid.UUID


class StudentIn(BaseModel):
    student_code: str = Field(min_length=2, max_length=30)
    first_name: str
    last_name: str | None = None
    date_of_birth: dt.date | None = None
    class_name: str
    section: str | None = None
    is_active: bool = True
    parents: list[ParentContactIn] = []


class StudentOut(StudentIn, Timestamped):
    parents: list[ParentContactOut] = []


class StudentFeePaymentIn(BaseModel):
    receipt_no: str
    period: str
    amount: float
    payment_mode: str


class StudentFeePaymentOut(StudentFeePaymentIn, Timestamped):
    student_id: uuid.UUID
    paid_at: dt.datetime


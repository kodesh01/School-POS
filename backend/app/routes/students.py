from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_roles
from app.db.session import get_db
from app.models.student import ParentContact, Student, StudentFeePayment
from app.schemas.common import Page, PageMeta
from app.schemas.student import StudentFeePaymentIn, StudentFeePaymentOut, StudentIn, StudentOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentOut], dependencies=[Depends(require_roles("Admin", "Staff", "Accountant"))])
async def list_students(
    db: AsyncSession = Depends(get_db),
    q: str | None = None,
    class_name: str | None = None,
    section: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[StudentOut]:
    stmt = select(Student).options(selectinload(Student.parents)).order_by(Student.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Student.first_name.ilike(like)) | (Student.last_name.ilike(like)) | (Student.student_code.ilike(like))
        )
    if class_name:
        stmt = stmt.where(Student.class_name == class_name)
    if section:
        stmt = stmt.where(Student.section == section)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    res = await db.execute(stmt.limit(limit).offset(offset))
    items = list(res.scalars().unique().all())
    return Page(items=items, meta=PageMeta(total=total, limit=limit, offset=offset))


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles("Admin", "Staff"))])
async def create_student(payload: StudentIn, db: AsyncSession = Depends(get_db)) -> StudentOut:
    existing = (await db.execute(select(Student).where(Student.student_code == payload.student_code))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="student_code already exists")

    student = Student(
        student_code=payload.student_code,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        class_name=payload.class_name,
        section=payload.section,
        is_active=payload.is_active,
    )
    for p in payload.parents:
        student.parents.append(ParentContact(**p.model_dump()))

    db.add(student)
    await db.commit()
    res = await db.execute(select(Student).where(Student.id == student.id).options(selectinload(Student.parents)))
    created = res.scalar_one()
    return created


@router.get("/{student_id}", response_model=StudentOut, dependencies=[Depends(require_roles("Admin", "Staff", "Accountant"))])
async def get_student(student_id: str, db: AsyncSession = Depends(get_db)) -> StudentOut:
    res = await db.execute(select(Student).where(Student.id == student_id).options(selectinload(Student.parents)))
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentOut, dependencies=[Depends(require_roles("Admin", "Staff"))])
async def update_student(student_id: str, payload: StudentIn, db: AsyncSession = Depends(get_db)) -> StudentOut:
    res = await db.execute(select(Student).where(Student.id == student_id).options(selectinload(Student.parents)))
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.student_code = payload.student_code
    student.first_name = payload.first_name
    student.last_name = payload.last_name
    student.date_of_birth = payload.date_of_birth
    student.class_name = payload.class_name
    student.section = payload.section
    student.is_active = payload.is_active

    student.parents.clear()
    for p in payload.parents:
        student.parents.append(ParentContact(**p.model_dump()))

    await db.commit()
    res = await db.execute(select(Student).where(Student.id == student.id).options(selectinload(Student.parents)))
    updated = res.scalar_one()
    return updated


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles("Admin"))])
async def delete_student(student_id: str, db: AsyncSession = Depends(get_db)) -> None:
    student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await db.delete(student)
    await db.commit()


@router.post(
    "/{student_id}/fees",
    response_model=StudentFeePaymentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("Admin", "Accountant"))],
)
async def add_fee_payment(student_id: str, payload: StudentFeePaymentIn, db: AsyncSession = Depends(get_db)) -> StudentFeePaymentOut:
    student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    payment = StudentFeePayment(student_id=student.id, **payload.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


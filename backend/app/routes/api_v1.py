from __future__ import annotations

from fastapi import APIRouter

from app.routes import auth, inventory, pos, reports, students, tax

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(inventory.router)
api_router.include_router(tax.router)
api_router.include_router(pos.router)
api_router.include_router(reports.router)


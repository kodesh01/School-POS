from __future__ import annotations

import datetime as dt
import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel


class APIModel(BaseModel):
    model_config = {"from_attributes": True}


class PageMeta(APIModel):
    total: int
    limit: int
    offset: int


T = TypeVar("T")


class Page(APIModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class IdResponse(APIModel):
    id: uuid.UUID


class Timestamped(APIModel):
    id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime


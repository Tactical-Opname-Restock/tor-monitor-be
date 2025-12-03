from typing import Optional, List
from datetime import datetime
from uuid import UUID
from sqlmodel import SQLModel

from .sales import SalesBase


class GoodsBase(SQLModel):
    id: UUID
    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int
    created_at: datetime


class GoodsAllResponse(SQLModel):
    data: list[GoodsBase]


class GoodsCreate(SQLModel):
    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int = 0


class GoodsUpdate(SQLModel):
    id: UUID
    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int


class GoodsDetail(GoodsBase):
    sales: Optional[List[SalesBase]] = None


class GoodsDetailResponse(SQLModel):
    data: GoodsDetail

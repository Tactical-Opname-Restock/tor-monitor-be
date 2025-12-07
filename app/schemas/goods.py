from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel

from .sales import SalesBase


class GoodsBase(SQLModel):
    """Base goods model"""

    id: UUID
    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int
    created_at: datetime


class GoodsCreate(SQLModel):
    """Request model untuk create goods"""

    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int = 0


class GoodsUpdate(SQLModel):
    """Request model untuk update goods"""

    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None


class GoodsDetail(GoodsBase):
    """Detail goods dengan sales relations"""

    sales: Optional[List[SalesBase]] = None


class GoodsAllResponse(SQLModel):
    """Response untuk GET /api/goods (list)"""

    data: list[GoodsBase]
    total: int
    page: int
    limit: int


class GoodsDetailResponse(SQLModel):
    """Response untuk GET /api/goods/{id}"""

    data: GoodsDetail


class GoodsCreateResponse(SQLModel):
    """Response untuk POST /api/goods"""

    message: str
    data: GoodsBase


class GoodsUpdateResponse(SQLModel):
    """Response untuk PUT /api/goods/{id}"""

    data: GoodsBase


class GoodsDeleteResponse(SQLModel):
    """Response untuk DELETE /api/goods/{id}"""

    message: str
    data: GoodsBase

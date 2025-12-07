from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel


class GoodsBase(SQLModel):
    """Goods info dalam sales"""

    id: UUID
    name: str
    category: Optional[str] = None


class SalesBase(SQLModel):
    """Base sales model"""

    id: UUID
    goods_id: UUID
    quantity: int
    sale_date: datetime
    total_profit: Optional[float] = None
    goods: GoodsBase


class SalesCreate(SQLModel):
    """Request model untuk create sales"""

    goods_id: UUID
    quantity: int
    sale_date: datetime


class SalesUpdate(SQLModel):
    """Request model untuk update sales"""

    quantity: Optional[int] = None
    sale_date: Optional[datetime] = None


class SalesAllResponse(SQLModel):
    """Response untuk GET /api/sales (list)"""

    data: list[SalesBase]
    total: int
    page: int
    limit: int


class SalesDetailResponse(SQLModel):
    """Response untuk GET /api/sales/{id}"""

    data: SalesBase


class SalesCreateResponse(SQLModel):
    """Response untuk POST /api/sales"""

    message: str
    data: SalesBase


class SalesUpdateResponse(SQLModel):
    """Response untuk PUT /api/sales/{id}"""

    data: SalesBase


class SalesDeleteResponse(SQLModel):
    """Response untuk DELETE /api/sales/{id}"""

    message: str
    data: SalesBase

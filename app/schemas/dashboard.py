from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class LowStockGood(SQLModel):
    """Barang dengan stok rendah"""

    id: UUID
    name: str
    category: Optional[str] = None
    stock_quantity: int
    price: float


class SalesChartPoint(SQLModel):
    """Point di chart sales"""

    date: str  # Format: YYYY-MM-DD
    total_quantity: int
    total_sales: float


class TopSellingItem(SQLModel):
    """Item paling laris dalam periode tertentu"""

    name: str
    total_quantity_sold: int
    total_profit: float


class DashboardData(SQLModel):
    """Data dashboard lengkap"""

    top_low_stock: List[LowStockGood]
    sales_chart: List[SalesChartPoint]
    monthly_revenue: float
    top_selling_item: TopSellingItem


class DashboardResponse(SQLModel):
    """Response dashboard"""

    data: DashboardData

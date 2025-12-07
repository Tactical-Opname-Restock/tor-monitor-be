from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import SQLModel


class SalesDatasetItem(SQLModel):
    """Single sales data point untuk forecast dataset (aggregated by date)"""

    date: str  # Format: YYYY-MM-DD
    total_quantity: int  # Total quantity sold on this date


class ForecastItem(SQLModel):
    """Single forecast prediction item"""

    date: str  # Format: YYYY-MM-DD
    total_sales: int  # Predicted sales quantity
    max_sales: int  # Upper bound prediction
    min_sales: int  # Lower bound prediction


class ForecastResult(SQLModel):
    """Complete forecast result dengan predictions dan statistics"""

    predictions: List[ForecastItem]  # List of predictions per day
    total_sales: int  # Total predicted sales quantity
    max_restock_quantity: int  # Maximum recommended restock quantity
    min_restock_quantity: int  # Minimum recommended restock quantity
    restock_quantity: int  # Recommended restock quantity
    goods_mae: Optional[float] = None  # Mean Absolute Error for this goods


class GoodsForecastData(SQLModel):
    """Goods item dengan sales history untuk forecast modeling"""

    id: UUID
    name: str
    category: Optional[str] = None
    price: float
    stock_quantity: int
    created_at: datetime
    sales: List[SalesDatasetItem]  # Historical sales data
    is_forecasted: bool  # Whether forecast is available
    forecast: Optional[ForecastResult] = None  # Forecast result with predictions


class ForecastResponse(SQLModel):
    """Response untuk GET /api/forecast/ - forecast data untuk goods with lowest stock"""

    data: List[GoodsForecastData]

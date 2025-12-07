from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import SQLModel


class RestockInferenceBase(SQLModel):
    """Base restock inference model"""

    id: UUID
    goods_id: UUID
    total_quantity: int
    future_preds: Optional[Dict] = None
    created_at: datetime


class RestockInferenceCreate(SQLModel):
    """Request model untuk create restock inference"""

    goods_id: UUID
    total_quantity: int
    future_preds: Optional[Dict] = None


class RestockInferenceUpdate(SQLModel):
    """Request model untuk update restock inference"""

    total_quantity: Optional[int] = None
    future_preds: Optional[Dict] = None


class RestockInferenceResponse(SQLModel):
    """Response untuk GET restock inference"""

    data: RestockInferenceBase


class RestockInferenceListResponse(SQLModel):
    """Response untuk list restock inferences"""

    data: list[RestockInferenceBase]


class RestockInferenceCreateResponse(SQLModel):
    """Response untuk POST restock inference"""

    message: str
    data: RestockInferenceBase


class RestockInferenceUpdateResponse(SQLModel):
    """Response untuk PUT restock inference"""

    data: RestockInferenceBase


class RestockInferenceDeleteResponse(SQLModel):
    """Response untuk DELETE restock inference"""

    message: str
    data: RestockInferenceBase

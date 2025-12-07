from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request model untuk POST /api/chat"""

    chat_message: str = Field(
        ...,
        description="Chat message dari user",
        min_length=1,
        max_length=5000,
    )


class ChatResponse(BaseModel):
    """Response model untuk POST /api/chat"""

    message: Optional[str] = None
    response: Optional[str] = None

    class Config:
        """Allow response to be either message or response field"""

        json_schema_extra = {
            "example": {
                "message": "Hai! Ada yang bisa saya bantu terkait pengelolaan barang atau penjualan Anda?"
            }
        }

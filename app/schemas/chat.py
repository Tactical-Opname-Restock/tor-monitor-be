from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Response model untuk POST /api/chat"""

    message: str
    response: str

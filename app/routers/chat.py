import logging

from fastapi import APIRouter, HTTPException

from ..dependencies import DBSessionDependency, UserDependency
from ..services.agent import AgentService
from ..schemas.chat import ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])
agent_service = AgentService()


@router.post("/api/chat")
def chat(
    db: DBSessionDependency, user: UserDependency, chat_message: str
) -> ChatResponse:
    try:
        response = agent_service.chat(prompt=chat_message, user_id=str(user.id), db=db)
        return {"message": chat_message, "response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing chat message")

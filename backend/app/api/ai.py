from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.message import AIQueryRequest
from app.services.ai_service import create_ai_response


router = APIRouter(prefix="/ai-query", tags=["ai"])


@router.post("")
def ai_query(payload: AIQueryRequest, current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "prompt": payload.prompt,
        "response": create_ai_response(payload.prompt),
    }

from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    message_type: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class AIQueryRequest(BaseModel):
    prompt: str

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageResponse


router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{other_user_id}", response_model=list[MessageResponse])
def get_messages(
    other_user_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(User, other_user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    statement = (
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id),
            )
        )
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    return list(reversed(db.scalars(statement).all()))

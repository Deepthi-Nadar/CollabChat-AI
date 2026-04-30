from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[UserResponse])
def search_users(
    query: str = Query(default="", max_length=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(User).where(User.id != current_user.id).order_by(User.username).limit(20)
    if query.strip():
        statement = statement.where(User.username.ilike(f"%{query.strip()}%"))
    return db.scalars(statement).all()

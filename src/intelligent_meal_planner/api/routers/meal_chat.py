from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import User
from ..schemas import MealChatMessageRequest, MealChatSessionResponse
from ..services import meal_chat_app
from .auth import get_current_user

router = APIRouter(prefix="/meal-chat", tags=["对话式配餐"])


@router.post("/sessions", response_model=MealChatSessionResponse)
async def create_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.start_session(db, current_user)


@router.get("/sessions/{session_id}", response_model=MealChatSessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = meal_chat_app.get_session(db, current_user, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/messages", response_model=MealChatSessionResponse)
async def send_message(
    session_id: str,
    payload: MealChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return meal_chat_app.handle_message(db, current_user, session_id, payload.content)

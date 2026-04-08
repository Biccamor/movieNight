from fastapi import APIRouter, HTTPException,status, Depends
from schemas.schemas import SavedPreferences
from scripts.security import decodeJWT
from scripts.uttils import check_if_email_exists
from sqlmodel import select
from database.main_db import get_session
from database.database_setup import User
from uuid import uuid4, UUID


router = APIRouter(prefix="/preferences", tags=['preferences'])


@router.post("/save", summary="Save the basic preferences of user for movies")
async def save_preferences(data: SavedPreferences, user_id: UUID, token: str, session = Depends(get_session)):
    
    if not decodeJWT(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = session.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.saved_preferences = data.model_dump()
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Preferences saved successfully", "user_id": user.user_id}


@router.get("/get", summary = "get preferences of user")
async def get_preferences(user_id: UUID, token: str, session = Depends(get_session)):
    
    if not decodeJWT(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = session.exec(select(User).where(User.user_id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.saved_preferences or {}

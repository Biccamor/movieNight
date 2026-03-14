from fastapi import APIRouter, Depends
from schemas import MovieSession
from database.main_db import get_session
from scripts.recommendation_service import RecomService

router = APIRouter(prefix="/recommendation", tags=["reccomendation"])

@router.post("/{group_id}")
async def get_recommendation(meta_data: MovieSession, session=Depends(get_session)) -> dict:

    return RecomService.get_recommend(meta_data, session)
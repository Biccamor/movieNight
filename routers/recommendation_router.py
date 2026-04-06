from fastapi import APIRouter, Depends
from schemas.schemas import MovieSession
from database.main_db import get_session
from engine.recommendation_service import RecomService

router = APIRouter(prefix="/recommendation", tags=["reccomendation"])

@router.post("/")
async def get_recommendation(meta_data: MovieSession, session=Depends(get_session)):

    recom_service = RecomService(meta_data, session)

    recommendation_movies = await recom_service._main()

    return recommendation_movies
    
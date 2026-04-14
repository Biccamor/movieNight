from fastapi import APIRouter, Depends, HTTPException, status, Request
from schemas.schemas import MovieSession
from database.main_db import get_session
from database.database_setup import Room_Session
from engine.recommendation_service import RecomService
from uuid import UUID
from scripts.security import get_current_user
from main import limiter

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.post("/session", summary="Zapisz sesję i preferencje do bazy")
@limiter.limit("20/minute")  # lekki endpoint — wiecej requestow dozwolone
async def save_session(request: Request, meta_data: MovieSession, user: dict = Depends(get_current_user), session=Depends(get_session)):
    """
    Przyjmuje dane sesji (użytkownicy, preferencje, typ spotkania),
    zapisuje je w bazie danych i zwraca session_id.
    Lekki endpoint nie wywołuje modeli AI.
    """
    recom_service = RecomService(meta_data, session)
    session_id = recom_service._add_db()
    return {"session_id": str(session_id)}


@router.post("/{session_id}", summary="Pobierz rekomendacje filmów dla sesji")
@limiter.limit("2/minute")  # ciezki endpoint AI — scisle limitowany
async def get_recommendation(request: Request, session_id: UUID, user: dict = Depends(get_current_user), session=Depends(get_session)):
    """
    Na podstawie wcześniej zapisanej sesji (session_id) wywołuje silnik AI
    i zwraca rekomendacje filmów.
    Ciężki endpoint może trwać dłużej ze względu na LLM.
    """

    db_session = session.get(Room_Session, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Sesja nie została znaleziona")

    recommendations = await RecomService.get_recommendations_from_db(db_session, session)
    return recommendations
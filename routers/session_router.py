from fastapi import APIRouter, Depends, HTTPException, status, Request
from schemas.schemas import (
    CreateSessionRequest, JoinSessionRequest, MemberPreferencesRequest,
    SessionResponse, SessionMemberResponse, Preferences,
    MovieSession, MovieSessionUser,
)
from database.main_db import get_session
from database.database_setup import MovieSessionDB, Room_Session, User
from engine.recommendation_service import RecomService
from scripts.security import get_current_user
from scripts.dependencies import limiter
from sqlmodel import select
from sqlalchemy.orm.attributes import flag_modified
from uuid import UUID, uuid4
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


# ─── Helpers ─────────────────────────────────────────────────────────

def _generate_invite_code(session, max_attempts: int = 10) -> str:
    """Generuje unikalny 6-znakowy kod zaproszenia."""
    for _ in range(max_attempts):
        code = secrets.token_urlsafe(4)[:6].upper()
        existing = session.exec(
            select(MovieSessionDB).where(MovieSessionDB.invite_code == code)
        ).first()
        if not existing:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Nie udało się wygenerować unikalnego kodu zaproszenia"
    )


def _get_movie_session(session_id: UUID, db_session) -> MovieSessionDB:
    """Pobiera sesję filmową z bazy lub rzuca 404."""
    movie_session = db_session.get(MovieSessionDB, session_id)
    if not movie_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesja nie została znaleziona"
        )
    return movie_session


def _is_member(movie_session: MovieSessionDB, user_id: str) -> bool:
    """Sprawdza czy użytkownik jest członkiem sesji."""
    return any(m["user_id"] == user_id for m in (movie_session.members or []))


def _build_session_response(movie_session: MovieSessionDB) -> SessionResponse:
    """Buduje odpowiedź API z modelu bazy danych."""
    members = [
        SessionMemberResponse(
            user_id=UUID(m["user_id"]),
            user_name=m["user_name"],
            status=m["status"],
            preferences=Preferences(**m["preferences"]) if m.get("preferences") else None,
        )
        for m in (movie_session.members or [])
    ]
    return SessionResponse(
        session_id=movie_session.session_id,
        host_id=movie_session.host_id,
        invite_code=movie_session.invite_code,
        meeting_type=movie_session.meeting_type,
        status=movie_session.status,
        members=members,
        recommendations=movie_session.recommendations,
        created_at=str(movie_session.created_at) if movie_session.created_at else None,
    )


# ─── Endpointy ──────────────────────────────────────────────────────

@router.post("/create", summary="Host tworzy nową sesję filmową")
@limiter.limit("10/minute")
async def create_session(
    request: Request,
    data: CreateSessionRequest,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Tworzy nową sesję filmową. Zalogowany użytkownik staje się hostem.
    Zwraca session_id i invite_code do udostępnienia innym.
    Host jest automatycznie dodawany jako członek sesji ze statusem 'pending'.
    """
    user_id = str(user["user_id"])
    db_user = session.exec(select(User).where(User.user_id == UUID(user_id))).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Użytkownik nie istnieje")

    invite_code = _generate_invite_code(session)
    session_id = uuid4()

    # Host jest też członkiem sesji
    host_member = {
        "user_id": user_id,
        "user_name": db_user.email.split("@")[0],  # prosty fallback na nazwę
        "status": "pending",
        "preferences": None,
    }

    new_session = MovieSessionDB(
        session_id=session_id,
        host_id=UUID(user_id),
        invite_code=invite_code,
        meeting_type=data.meeting_type,
        status="LOBBY",
        members=[host_member],
    )

    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    logger.info(f"Sesja {session_id} utworzona przez {user_id} z kodem {invite_code}")

    return {
        "session_id": str(session_id),
        "invite_code": invite_code,
        "meeting_type": data.meeting_type,
    }


@router.post("/join", summary="Dołącz do sesji kodem zaproszenia")
@limiter.limit("15/minute")
async def join_session(
    request: Request,
    data: JoinSessionRequest,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Dołącza zalogowanego użytkownika do sesji na podstawie invite_code.
    Użytkownik jest dodawany ze statusem 'pending' — musi jeszcze podać preferencje.
    """
    user_id = str(user["user_id"])
    code = data.invite_code.strip().upper()

    # Znajdź sesję po kodzie
    movie_session = session.exec(
        select(MovieSessionDB).where(MovieSessionDB.invite_code == code)
    ).first()

    if not movie_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nieprawidłowy kod zaproszenia"
        )

    if movie_session.status != "LOBBY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sesja nie przyjmuje nowych członków (nie jest w stanie LOBBY)"
        )

    # Sprawdź czy user już jest w sesji
    if _is_member(movie_session, user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Już jesteś członkiem tej sesji"
        )

    # Pobierz dane usera
    db_user = session.exec(select(User).where(User.user_id == UUID(user_id))).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Użytkownik nie istnieje")

    new_member = {
        "user_id": user_id,
        "user_name": db_user.email.split("@")[0],
        "status": "pending",
        "preferences": None,
    }

    members = list(movie_session.members or [])
    members.append(new_member)
    movie_session.members = members
    flag_modified(movie_session, "members")

    session.add(movie_session)
    session.commit()
    session.refresh(movie_session)

    logger.info(f"Użytkownik {user_id} dołączył do sesji {movie_session.session_id}")

    return {
        "message": "Dołączono do sesji",
        "session_id": str(movie_session.session_id),
        "meeting_type": movie_session.meeting_type,
    }


@router.put("/{session_id}/preferences", summary="Zapisz preferencje i zmień status na ready")
@limiter.limit("15/minute")
async def set_member_preferences(
    request: Request,
    session_id: UUID,
    data: MemberPreferencesRequest,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Członek sesji podaje swoje preferencje na tę sesję.
    Po zapisaniu status członka zmienia się na 'ready'.
    Jeśli wszyscy członkowie mają status 'ready', status sesji zmienia się na 'ALL_READY'.
    """
    user_id = str(user["user_id"])
    movie_session = _get_movie_session(session_id, session)

    if movie_session.status not in ("LOBBY", "ALL_READY"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sesja nie przyjmuje już preferencji"
        )

    # Znajdź członka i zaktualizuj
    members = list(movie_session.members or [])
    member_found = False
    for member in members:
        if member["user_id"] == user_id:
            member["preferences"] = data.preferences.model_dump()
            member["status"] = "ready"
            member_found = True
            break

    if not member_found:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie jesteś członkiem tej sesji"
        )

    movie_session.members = members
    flag_modified(movie_session, "members")

    # Sprawdź czy wszyscy są ready
    all_ready = all(m["status"] == "ready" for m in members)
    if all_ready:
        movie_session.status = "ALL_READY"

    session.add(movie_session)
    session.commit()
    session.refresh(movie_session)

    logger.info(f"Preferencje użytkownika {user_id} zapisane w sesji {session_id}. All ready: {all_ready}")

    return {
        "message": "Preferencje zapisane, status: ready",
        "all_ready": all_ready,
        "session_status": movie_session.status,
    }


@router.get("/{session_id}", summary="Pobierz stan sesji", response_model=SessionResponse)
@limiter.limit("30/minute")
async def get_session_details(
    request: Request,
    session_id: UUID,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Zwraca pełny stan sesji — członkowie, ich statusy, preferencje i ewentualne rekomendacje.
    Dostępne dla hosta i wszystkich członków sesji.
    """
    user_id = str(user["user_id"])
    movie_session = _get_movie_session(session_id, session)

    # Sprawdź czy user jest hostem lub członkiem
    is_host = str(movie_session.host_id) == user_id
    is_member_flag = _is_member(movie_session, user_id)

    if not is_host and not is_member_flag:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz dostępu do tej sesji"
        )

    return _build_session_response(movie_session)


@router.post("/{session_id}/recommend", summary="Wywołaj rekomendacje AI (tylko host, wszyscy ready)")
@limiter.limit("2/minute")
async def trigger_recommendations(
    request: Request,
    session_id: UUID,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Host wywołuje rekomendacje filmów dla sesji.
    Wymaga: wszyscy członkowie muszą mieć status 'ready'.
    Wewnętrznie tworzy Room_Session, wywołuje RecomService i zapisuje wyniki.
    """
    user_id = str(user["user_id"])
    movie_session = _get_movie_session(session_id, session)

    # Tylko host może wywołać rekomendacje
    if str(movie_session.host_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko host może wywołać rekomendacje"
        )

    # Sprawdź czy wszyscy ready
    members = movie_session.members or []
    if not members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sesja nie ma członków"
        )

    not_ready = [m["user_name"] for m in members if m["status"] != "ready"]
    if not_ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nie wszyscy członkowie są gotowi. Oczekiwanie na: {', '.join(not_ready)}"
        )

    if movie_session.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rekomendacje zostały już wygenerowane dla tej sesji"
        )

    # Zmień status na RECOMMENDING
    movie_session.status = "RECOMMENDING"
    session.add(movie_session)
    session.commit()

    try:
        # Zbuduj MovieSessionUser-ów z preferencji członków
        session_users = []
        for m in members:
            prefs = m.get("preferences") or {}
            session_users.append(
                MovieSessionUser(
                    user_id=UUID(m["user_id"]),
                    user_name=m["user_name"],
                    personal_vibe=Preferences(**prefs),
                )
            )

        # Zbuduj MovieSession dla RecomService (istniejący schemat)
        invite_code = movie_session.invite_code
        meta_data = MovieSession(
            host_id=movie_session.host_id,
            session_id=uuid4(),  # nowy ID dla Room_Session
            invite_code=invite_code,
            meeting_type=movie_session.meeting_type,
            users=session_users,
        )

        # 1. Zapisz Room_Session (embedding, wektor grupowy, itp.)
        recom_service = RecomService(meta_data, session)
        room_session_id = await recom_service._add_db()

        # 2. Pobierz rekomendacje AI
        db_room_session = session.get(Room_Session, room_session_id)
        if not db_room_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Błąd wewnętrzny — nie znaleziono Room_Session po zapisie"
            )

        recommendations = await RecomService.get_recommendations_from_db(db_room_session, session)

        if isinstance(recommendations, dict):
            rec_data = recommendations.get("recommendations", [recommendations])
        elif isinstance(recommendations, list):
            rec_data = recommendations
        else:
            rec_data = [recommendations] if recommendations else []

        rec_data_dicts = []
        for r in rec_data:
            if hasattr(r, "model_dump"):
                # Konwertujemy Pydantic do słownika
                # model_dump(mode='json') konwertuje też UUID i daty na stringi, 
                # co zapobiega kolejnym błędom serializacji JSONB.
                rec_data_dicts.append(r.model_dump(mode='json'))
            elif hasattr(r, "dict"):
                rec_data_dicts.append(r.dict())
            else:
                rec_data_dicts.append(r)

        movie_session.recommendations = rec_data_dicts
        movie_session.room_session_id = room_session_id
        movie_session.status = "COMPLETED"

        session.add(movie_session)
        session.commit()
        session.refresh(movie_session)

        logger.info(f"Rekomendacje wygenerowane dla sesji {session_id}")

        return {
            "message": "Rekomendacje wygenerowane",
            "session_id": str(session_id),
            "room_session_id": str(room_session_id),
            "recommendations": rec_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Błąd podczas generowania rekomendacji dla sesji {session_id}: {e}")
        # Rollback statusu
        movie_session.status = "ALL_READY"
        session.add(movie_session)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas generowania rekomendacji: {str(e)}"
        )


@router.delete("/{session_id}", summary="Zamknij/anuluj sesję (tylko host)")
@limiter.limit("10/minute")
async def delete_session(
    request: Request,
    session_id: UUID,
    user: dict = Depends(get_current_user),
    session=Depends(get_session),
):
    """
    Host zamyka sesję filmową. Sesja zostaje usunięta z bazy.
    """
    user_id = str(user["user_id"])
    movie_session = _get_movie_session(session_id, session)

    if str(movie_session.host_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko host może zamknąć sesję"
        )

    session.delete(movie_session)
    session.commit()

    logger.info(f"Sesja {session_id} zamknięta przez hosta {user_id}")

    return {"message": "Sesja została zamknięta", "session_id": str(session_id)}

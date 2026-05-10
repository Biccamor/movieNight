import asyncio
from sqlmodel import select, Session
import scripts.dependencies as d
from database.database_setup import MovieSessionDB, Room_Session
from engine.recommendation_service import RecomService
from schemas.schemas import MovieSession, MovieSessionUser, Preferences
from uuid import uuid4

async def main():
    d.load_db()
    d.load_model()
    d.load_reranker()
    with Session(d.engine) as session:
        movie_session = session.exec(select(MovieSessionDB).order_by(MovieSessionDB.created_at.desc()).limit(1)).first()
        if not movie_session:
            print("No sessions found.")
            return

        print("Testing session:", movie_session.session_id)
        members = movie_session.members or []
        session_users = []
        for m in members:
            prefs = m.get("preferences") or {}
            session_users.append(
                MovieSessionUser(
                    user_id=m["user_id"],
                    user_name=m["user_name"],
                    personal_vibe=Preferences(**prefs),
                )
            )

        meta_data = MovieSession(
            host_id=movie_session.host_id,
            session_id=uuid4(),
            invite_code=movie_session.invite_code,
            meeting_type=movie_session.meeting_type,
            users=session_users,
        )

        try:
            recom_service = RecomService(meta_data, session)
            room_session_id = await recom_service._add_db()
            
            db_room_session = session.get(Room_Session, room_session_id)
            recommendations = await RecomService.get_recommendations_from_db(db_room_session, session)

            if isinstance(recommendations, dict):
                rec_data = recommendations.get("recommendations", [recommendations])
            elif isinstance(recommendations, list):
                rec_data = recommendations
            else:
                rec_data = [recommendations] if recommendations else []

            movie_session.recommendations = rec_data
            movie_session.room_session_id = room_session_id
            movie_session.status = "COMPLETED"

            session.add(movie_session)
            session.commit()
            print("Success!")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

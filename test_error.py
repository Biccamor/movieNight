import asyncio
from sqlmodel import select, Session
import scripts.dependencies as d
from database.database_setup import Room_Session
from engine.recommendation_service import RecomService

async def main():
    d.load_db()
    d.load_reranker()
    with Session(d.engine) as session:
        statement = select(Room_Session).order_by(Room_Session.created_at.desc()).limit(1)
        db_session = session.exec(statement).first()
        
        if not db_session:
            print("No sessions found.")
            return

        print(f"Testing session: {db_session.session_id}")
        try:
            res = await RecomService.get_recommendations_from_db(db_session, session)
            print("Success!")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

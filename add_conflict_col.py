import asyncio
from sqlmodel import Session, text
import scripts.dependencies as d

def alter_table():
    d.load_db()
    with Session(d.engine) as session:
        try:
            session.exec(text("ALTER TABLE room_session ADD COLUMN conflict BOOLEAN DEFAULT FALSE;")) # type: ignore
            session.commit()
            print("Successfully added conflict column.")
        except Exception as e:
            print("Error or column already exists:", e)

if __name__ == "__main__":
    alter_table()

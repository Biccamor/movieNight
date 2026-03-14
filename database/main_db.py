from sqlmodel import create_engine, SQLModel, Session, text
from database.database_setup import User, Movie, Rating, Room_Session
engine = create_engine("postgresql://my_user:my_pwd@localhost:5432/my_db", echo=True)

def create_tables():    
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS VECTOR"))
        session.commit()
    SQLModel.metadata.create_all(engine)    
    with Session(engine) as session:

        session.exec(text(" CREATE INDEX IF NOT EXISTS hnsw_movie" \
                        " ON movie USING hnsw "
                        " (embedding vector_cosine_ops)" \
                        " WITH (m = 16, ef_construction = 128); "))
        session.commit()


def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    create_tables()
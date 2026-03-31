from sqlmodel import SQLModel, Session, text
import scripts.dependencies as d 

def create_tables():    
    with Session(d.engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS VECTOR")) # type: ignore
        session.commit()
    SQLModel.metadata.create_all(engine)    # type: ignore
    with Session(d.engine) as session:

        session.exec(text(" CREATE INDEX IF NOT EXISTS hnsw_movie" \
                        " ON movie USING hnsw "
                        " (embedding vector_cosine_ops)" \
                        " WITH (m = 16, ef_construction = 128); ")) # type: ignore
        session.commit()


def get_session():
    with Session(d.engine) as session:
        yield session

if __name__ == "__main__":
    create_tables()
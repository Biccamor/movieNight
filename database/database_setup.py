from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import UniqueConstraint
from uuid import UUID, uuid4
from pgvector.sqlalchemy import Vector
from datetime import date

class User(SQLModel, table=True):
    """
        Table for users postgresql containig:
        user_id - primary key
        email - unique
        hash_password
    """
    __table_args__ = (UniqueConstraint("email"),)
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hash_password: str

    user_taste: list[float] | None = Field(sa_column=Column(Vector(768)), default=None)

class Movies(SQLModel, table=True):

    movie_id: UUID = Field(default_factory=uuid4, primary_key=True)
    tmdb_id: int = Field(unique=True, index=True)

    title: str  = Field(index=True)
    description: str | None = Field(default=None)
    genre: list[str] | None = Field(default_factory=list, sa_column=Column(JSON))
    poster_path: str| None = Field(default=None)
    release_date: date | None = Field(default=None)
    runtime: int | None = Field(default=None, index=True)

    #TODO in future change Vector to 1536 (OPENAI API)
    embedding: list[float] | None = Field(sa_column=Column(Vector(768), default=None))

class Session(SQLModel,table=True):

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    is_active: bool = Field(default=True)
    recomended_runtime: int | None = Field(default=None, index=True)
    min_runtime: int | None = Field(default=None, index=True)
    occasion: str | None = Field(default=None, index=True)
    allow_seen: dict[str, bool] = Field(default_factory=dict, sa_column=Column(JSON))

    preferences: dict | None= Field(default_factory=dict, sa_column=Column(JSON))
    created_at: date | None = Field(default_factory=date.today)

    users_in_session: list[UUID] = Field(default_factory=list, sa_column=Column(JSON))
    embedding_preferences: list[float] | None = Field(sa_column=Column(Vector(768)), default=None)


class Rating(SQLModel, table=True):
    rating_id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    user_id: UUID = Field(foreign_key="user.user_id", index=True)
    movie_id: UUID = Field(foreign_key="movies.movie_id", index=True)
    session_id: UUID = Field(foreign_key="session.session_id", index=True)
    
    rated_at: date | None = Field(default_factory=date.today)
    # -1 = dislike 0 = have seen no opinion 1 = like 
    rating: int = Field(default=0, index=True) 

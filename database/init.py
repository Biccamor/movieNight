from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class User(SQLModel, table=True):
    """
        Table for users postgresql containig:
        user_id - primary key
        email - unique
        hash_password
    """
    __table_args__ = (UniqueConstraint("email"),)
    user_id: int | None = Field(default=None, primary_key=True)
    email: str
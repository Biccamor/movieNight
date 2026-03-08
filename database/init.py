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
    email: str = Field(unique=True, index=True)
    hash_password: str

def create_tables():
    engine = "postgresql://my_user:my_pwd@localhost:5432/my_db"
    SQLModel.metadata.create_all(engine)    
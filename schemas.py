from pydantic import BaseModel 
from uuid import uuid4

class Preferences(BaseModel):
    genre_likes: list[str]
    genre_dislikes: list[str]
    time: list[str]

class User(BaseModel):
    user_name: str
    preferences: Preferences

class Data(BaseModel):
    meeting: str
    id: uuid4
    users: list[User]
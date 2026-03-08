from pydantic import BaseModel 
from uuid import uuid4

"""
Przyklad danych:

[id: 12asda3as367696969, typ_spotkania: "ruchanie", {user: "KarolZwyrtek", preferences: {genre_likes: [], 
genre_dislike: [kobiety, mozg], time: [30 sekund] } ]

"""


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
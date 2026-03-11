from typing import Self

from pydantic import BaseModel, Field, EmailStr, model_validator
from uuid import uuid4, UUID
from pydantic_settings import BaseSettings, SettingsConfigDict
"""
Przyklad danych:

[id: 12asda3as367696969, typ_spotkania: "ruchanie", {user: "KarolZwyrtek", preferences: {genre_likes: [], 
genre_dislike: [kobiety, mozg], time: [30 sekund] } ]

"""


class Preferences(BaseModel):
    genre_likes: list[str]
    genre_dislikes: list[str]
    allow_seen: bool = Field(default=False)
    time: int

class User(BaseModel):
    user_id: UUID
    user_name: str
    preferences: Preferences

class Data(BaseModel):
    meeting: str
    id: UUID
    users: list[User]

class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, title="Your password must have at least 8 characters", max_length=100)
    confirm_password: str

    @model_validator(mode="after")
    def password_match(self) -> Self:
        if self.password == self.confirm_password:
            return self
    
        return ValueError("Passwords don't match") 

class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, title="Enter your password")

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire: int = 25
    
    model_config = SettingsConfigDict(env_file=".env")


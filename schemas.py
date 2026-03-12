from typing import Self, List, Literal, Optional

from pydantic import BaseModel, Field, EmailStr, model_validator
from uuid import uuid4, UUID
from pydantic_settings import BaseSettings, SettingsConfigDict

class UserPreferences(BaseModel):

    vibes: List[Literal["PIZZA_CHILL", "MIND_BENDER", "ADRENALINE", "DATE_NIGHT", "DEEP_FEELS"]]
    hard_nos: List[Literal["SLOW_BURN", "GORE", "SAD_ENDING", "KIDS_STUFF"]] = Field(default_factory=list)
    max_runtime: int = Field(default=120, ge=30, le=240)
    allow_seen: bool = False


class SessionUser(BaseModel):
    user_id: UUID
    user_name: str
    personal_vibe: UserPreferences


class MovieSession(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    invite_code: str  # Np. "XJ79B" - do wejścia przez kod/QR
    
    meeting_type: Literal["RANDKA", "EKIPA", "RODZINA", "SOLO"]
    
    is_active: bool = True
    users: List[SessionUser] = Field(default_factory=list)
    
    final_preferences: Optional[UserPreferences] = None

class CreateSessionRequest(BaseModel):
    host_id: UUID
    meeting_type: Literal["RANDKA", "EKIPA", "RODZINA", "SOLO"]

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


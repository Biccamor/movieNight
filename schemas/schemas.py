from typing import Self, List, Literal, Optional

from pydantic import BaseModel, Field, EmailStr, model_validator
from uuid import uuid4, UUID
from pydantic_settings import BaseSettings, SettingsConfigDict

VibeType = Literal["PIZZA_CHILL", "MIND_BENDER", "ADRENALINE", "DATE_NIGHT", "DEEP_FEELS", "LAUGH_RIOT", "SPINE_CHILLING", "NOSTALGIA", "INSPIRING", "EPIC_JOURNEY", "GUILTY_PLEASURE"]

class Preferences(BaseModel): #podawane przy nowym requescie/sesji
    vibes: List[VibeType] = Field(default_factory=list)
    hard_nos: List[VibeType] = Field(default_factory=list)
    max_runtime: int = Field(default=120, ge=30, le=240)
    allow_seen: bool = False
    eras: List[str] = Field(default_factory=list)

class SavedPreferences(BaseModel): #jednorazowo podane przy rejestracji
    vibes: List[VibeType] = Field(default_factory=list)
    hard_nos: List[VibeType] = Field(default_factory=list)
    eras: List[str] = Field(default_factory=list)
    movies: List[str] = Field(default_factory=list)

class User(BaseModel):
    email: EmailStr #haslo jest przywiazane do maila nie usera
    user_id: UUID
    user_name: str
    saved_preferences: SavedPreferences
    profile_picture: Optional[str] = None #zgnieciony obrazek do profilu

class MovieRequest(BaseModel): #pojedynczy request o film niekoniecznie z sesji
    user_id: UUID
    final_preferences: Preferences

class MovieSessionUser(BaseModel): #czlonek sesji
    user_id: UUID
    user_name: str
    personal_vibe: Preferences

class GhostUser(BaseModel): #czlonek sesji ktory nie jest zalogowany (coming soon)
    user_name: str
    personal_vibe: Preferences

class MovieSession(BaseModel): #sesja od jednego uzytkownika do ktorej dolaczyc moze wiecej
    host_id: UUID
    session_id: UUID = Field(default_factory=uuid4)
    invite_code: str  # Np. "XJ79B" - do wejścia przez kod/QR
    
    meeting_type: Literal["RANDKA", "EKIPA", "RODZINA", "SOLO"]
    
    is_active: bool = True
    users: List[MovieSessionUser] = Field(default_factory=list)
    
    final_preferences: Optional[Preferences] = None

class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, title="Your password must have at least 8 characters", max_length=100)
    confirm_password: str

    @model_validator(mode="after")
    def password_match(self) -> Self:
        if self.password == self.confirm_password:
            return self
    
        raise ValueError("Passwords don't match")

class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, title="Enter your password")

class AppSettings(BaseModel):
    theme: Literal["DARK", "LIGHT", "SYSTEM"] = "LIGHT"

class Settings(BaseSettings):
    database_url: str
    ollama_base_url: str
    secret_key: str
    algorithm: str
    access_token_expire: int = 25
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


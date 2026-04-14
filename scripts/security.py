from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from schemas.schemas import Settings
import datetime
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

setting = Settings() # type: ignore
ph = PasswordHasher()
security = HTTPBearer()
logger = logging.getLogger(__name__)

def hash_password(password: str):
    """Zamiana hasła podanego przez uzytkownika na hash"""
    hashed = ph.hash(password=password)
    return hashed

def verify_password(hashed_password: str, password: str) -> bool:
    """Sprawdzenie czy uzytkownik podal poprawne haslo"""

    try:
        ph.verify(hashed_password, password)
        return True
    
    except VerifyMismatchError: # złe hasło po prostu
        return False
    
    except Exception as e:
        logger.error(f"ERROR {e}")
        return False

def token_response(token: str):
    return {
        "access_token": token
    }

def signJWT(user_id: str) -> dict:
    """Tworzy krótkożyjący access token (domyślnie 25 min)."""
    payload = {
        "user_id": str(user_id),
        "type": "access",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=setting.access_token_expire)
    }
    token = jwt.encode(payload, setting.secret_key, algorithm=setting.algorithm)

    return token_response(token)

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.error("Token wygasł!")
        return {}
    except jwt.InvalidTokenError:
        logger.error("Nieprawidłowy token!")
        return {}
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """ funkcja do wyciagania tokenu usera z HTTP """
    
    token = credentials.credentials

    payload = decodeJWT(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def get_rate_limit_key(request) -> str:

    """
    key_func dla slowapi — identyfikuje usera po user_id z JWT tokena.
    Fallback na IP jeśli brak tokena (np. /login, /register).
    """
    auth: str = request.headers.get("Authorization", "") # pobieramy token z naglowka
    if auth.startswith("Bearer "):
        token = auth.removeprefix("Bearer ")
        payload = decodeJWT(token)
        user_id = payload.get("user_id")
        if user_id:
            return str(user_id)
    # fallback na IP dla publicznych endpointów
    return request.client.host if request.client else "unknown"

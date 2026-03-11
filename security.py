from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from schemas import Settings
import datetime

setting = Settings()
ph = PasswordHasher()

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
        print("ERROR {e}")
        return False

def token_response(token: str):
    return {
        "access_token": token
    }

def signJWT(user_id: str) -> dict:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=setting.access_token_expire)
    }
    token = jwt.encode(payload, setting.secret_key, algorithm=setting.algorithm)

    return token_response(token)

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])
        return decoded_token
    except jwt.ExpiredSignatureError:
        print("Token wygasł!")
        return {}
    except jwt.InvalidTokenError:
        print("Nieprawidłowy token!")
        return {}
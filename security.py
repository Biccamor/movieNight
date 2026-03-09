from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

def hash_password(password: str):
    """Zamiana hasła podanego przez uzytkownika na hash"""
    ph = PasswordHasher()
    hashed = ph.hash(password=password)
    return hashed

def verify_password(hashed_password: str, password: str) -> bool:
    """Sprawdzenie czy uzytkownik podal poprawne haslo"""

    ph = PasswordHasher()

    try:
        ph.verify(hashed_password, password)
        return True
    
    except VerifyMismatchError: # złe hasło po prostu
        return False
    
    except Exception as e:
        print("ERROR {e}")
        return False
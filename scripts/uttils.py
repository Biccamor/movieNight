from sqlmodel import select, Session
from database.database_setup import User, Room_Session
from database.main_db import engine

# TODO: sprawdz czy napewno dobry jest ten user

def check_if_email_exists(email: str, session) -> bool:

    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    
    return existing_user is not None
    
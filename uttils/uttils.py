from sqlmodel import select
from schemas import User
from database.database_setup import Session

def check_if_email_exists(email: str, session: Session) -> bool:

    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    return existing_user == None
    
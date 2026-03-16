from sqlmodel import select
from database.database_setup import User, Room_Session

# TODO: sprawdz czy napewno dobry jest ten user

def check_if_email_exists(email: str, session: Room_Session) -> bool:

    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    return existing_user == None
    
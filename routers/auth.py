from fastapi import APIRouter, HTTPException,status, Depends
from schemas import Register, Login
from security import hash_password, verify_password
from sqlmodel import select, Session
from database.main import get_session
from database.init import User
from uuid import uuid4

router = APIRouter(prefix="auth", tags=['auth'])

def check_if_email_exists(email: str, session: Session) -> bool:

    statement = select(User).where(User.email == email)
    
    existing_user = session.exec(statement).first()

    return existing_user is not None 

@router.post("register")
async def create_account(data: Register, session = Depends(get_session)):
    
    if check_if_email_exists(data.email, session=session) == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik o takim adresie e-mail już istnieje."
        )
    
    hashed_password = hash_password(data.password)
    new_user = User(user_id = str(uuid4()), email = data.email, hash_password=hashed_password)
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "Account created successfully", "user_id": new_user.id}


@router.post("login")
async def login_account():
    ...
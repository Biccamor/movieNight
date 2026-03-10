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
    return existing_user == None
    
@router.post("register")
async def create_account(data: Register, session = Depends(get_session)):
    
    if check_if_email_exists(data.email, session=session) == True:
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
async def login_account(data: Login, session = Depends(get_session)):
    
    statement = select(User).where(User.email == data.email)
    get_user = session.exec(statement).first()
    
    login_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy e-mail lub hasło",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not get_user:
        raise login_error


    db_password = get_user.hash_password

    check_password = verify_password(hashed_password=db_password, password=data.password)
    if check_password == False:
        raise login_error
    
    return {"message": "User {data.mail} logged in", "user_id": data.user_id}

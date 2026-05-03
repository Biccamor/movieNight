from fastapi import APIRouter, HTTPException, status, Depends, Request
from schemas.schemas import Register, Login, RefreshRequest
from scripts.security import hash_password, verify_password, signJWT, verify_refresh_token
from scripts.uttils import check_if_email_exists
from sqlmodel import select
from database.main_db import get_session
from database.database_setup import User
from uuid import uuid4
from scripts.dependencies import limiter

router = APIRouter(prefix="/auth", tags=['auth'])


@router.post("/register")
@limiter.limit("5/minute")  # max 5 rejestracji/min z jednego IP
async def create_account(request: Request, data: Register, session = Depends(get_session)):
    
    if check_if_email_exists(data.email, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email adress already exists"
        )
    
    hashed_password = hash_password(data.password)
    new_user = User(user_id = uuid4(), email = data.email, hash_password=hashed_password)
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "Account created successfully", "user_id": new_user.user_id}


@router.post("/login")
@limiter.limit("10/minute")  # max 10 prob logowania/min — ochrona brute force
async def login_account(request: Request, data: Login, session = Depends(get_session)):
    
    statement = select(User).where(User.email == data.email)
    get_user = session.exec(statement).first()
    
    login_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong e-mail or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not get_user:
        raise login_error

    db_password = get_user.hash_password

    check_password = verify_password(hashed_password=db_password, password=data.password)
    if check_password == False:
        raise login_error
    
    token = signJWT(get_user.user_id)

    return {
        "message": f"User {data.email} logged in",
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],
        "token_type": "bearer",
        "user_id": get_user.user_id,
    }


@router.post("/refresh", summary="Odśwież access token przy użyciu refresh tokena")
@limiter.limit("5/minute")  # chronimy przed masowym odświeżaniem
async def refresh_access_token(request: Request, data: RefreshRequest):
    """
    Przyjmuje refresh_token, weryfikuje go i wydaje nową parę
    (access_token + refresh_token) — tzw. token rotation.
    """
    payload = verify_refresh_token(data.refresh_token)
    user_id = payload["user_id"]

    new_tokens = signJWT(user_id)
    return {
        "access_token": new_tokens["access_token"],
        "refresh_token": new_tokens["refresh_token"],
        "token_type": "bearer",
    }


from fastapi import APIRouter

router = APIRouter(prefix="auth", tags=['auth'])


@router.post("register")
async def create_account():
    ...


@router.post("login")
async def login_account():
    ...
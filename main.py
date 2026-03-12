from fastapi import FastAPI
from routers.recommendation import router as recommendation_router
from routers.auth import router as auth_router

app = FastAPI()
app.include_router(recommendation_router)
app.include_router(auth_router)

@app.get("/")
async def main():
    return "Server dziala"
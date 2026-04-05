from fastapi import FastAPI, Request
from routers.recommendation_router import router as recommendation_router
from routers.auth_router import router as auth_router
from routers.metadata_router import router as metadata_router
import time
import logging
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import scripts.dependencies as d
from database.main_db import create_tables

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        d.load_model()
        d.load_db()
        create_tables()
        yield
    except Exception as e:
        logger.exception(f"Startup failed: {e}")
        raise
    finally:
        pass



app = FastAPI(lifespan=lifespan)
app.include_router(recommendation_router)
app.include_router(auth_router)
app.include_router(metadata_router)



origins = [
    "https://groupmovie.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: zmienic przed deployem ale do testow zostawic
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    return "Server dziala"

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
from sentence_transformers import SentenceTransformer
from flashrank import Ranker
from sqlmodel import create_engine
from dotenv import load_dotenv
import os
from slowapi import Limiter
from scripts.security import get_rate_limit_key
model: SentenceTransformer = None # type: ignore
engine = None
reranker: Ranker = None #type: ignore
limiter = Limiter(key_func=get_rate_limit_key, default_limits=["100/minute"])
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def load_model():
    global model
    model = SentenceTransformer('BAAI/bge-base-en-v1.5')

def load_reranker():
    global reranker
    reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")

def load_db():
    global engine 
    engine = create_engine(DATABASE_URL, #type: ignore
                        echo=False,
                        pool_size=20,          
                        max_overflow=10,      
                        pool_timeout=60,      
                        pool_recycle=1800,)
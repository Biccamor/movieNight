from ollama import chat, Client
from engine.prompts import AGENT_SYSTEM_PROMPT
from engine.vector import hybrid_search
from pydantic import BaseModel
from enum import Enum
import os

client = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

class MovieRecommendation(BaseModel):
    thought: str
    movie_title: str
    reasoning_pl: str
    extra_movies: str
def decide(session, query, runtime: int, prompt: str,  rating_weight:float=0.25, limit_movies:int = 50):
    

    search = hybrid_search(query, runtime, session, rating_weight, limit_movies)
    movies_list = [answer['movie'] for answer in search]
    movies_str = ", ".join(movies_list)

    model = "gemma2:2b"

    response = client.chat(
        model=model,
        messages=[
            {'role': 'system', 
             'content': AGENT_SYSTEM_PROMPT},
            {'role': 'user', 
             'content': f"Movies you can choose from {movies_str}\n {prompt}" }
                ],

            format=MovieRecommendation.model_json_schema()
        )
    
    return MovieRecommendation.model_validate_json(response.message.content) # type: ignore
    
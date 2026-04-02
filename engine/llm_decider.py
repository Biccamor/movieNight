from ollama import Client
from engine.prompts import AGENT_SYSTEM_PROMPT
from engine.vector import hybrid_search
from pydantic import BaseModel
import os

client = Client(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

class ExtraMovie(BaseModel):
    movie_title: str 
    genres: list[str]
    poster_path: str

class MovieRecommendation(BaseModel):
    thought: str
    movie_title: str
    reasoning_pl: str
    extra_movies: list[ExtraMovie]
    poster_path: str
    genres: list[str]

def decide(session, query, runtime: int, prompt: str,  rating_weight:float=0.25, limit_movies:int = 50):
    

    search = hybrid_search(query, runtime, session, rating_weight, limit_movies)
    movies_str = "\n".join([
    f"- title: {f['movie']} | genre: {f.get('genre', '')} | poster_path: {f.get('poster_path', '')}"
    for f in search
])

    model = "gemma2:2b"

    response = client.chat(
        model=model,
        messages=[
            {'role': 'system', 
             'content': AGENT_SYSTEM_PROMPT.replace("{group_preferences_input}", prompt)},
            {'role': 'user', 
             'content': f"Movies you can choose from {movies_str}\n {prompt}" }
                ],

            format=MovieRecommendation.model_json_schema()
        )
    
    return MovieRecommendation.model_validate_json(response.message.content) # type: ignore
    
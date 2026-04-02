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

def decide(session, query, runtime: int, prompt: str, rating_weight: float = 0.25, limit_movies: int = 50):
    
    search = hybrid_search(query, runtime, session, rating_weight, limit_movies)
    
    # lookup po tytule dla wszystkich filmów
    movie_lookup = {f['movie']: f for f in search}
    
    movies_str = "\n".join([
        f"- title: {f['movie']} | genre: {f.get('genre', '')}"
        for f in search
    ])

    response = client.chat(
        model="gemma2:2b",
        messages=[
            {'role': 'system', 
             'content': AGENT_SYSTEM_PROMPT.replace("{group_preferences_input}", prompt)},
            {'role': 'user', 
             'content': f"Movies you can choose from:\n{movies_str}\n{prompt}"}
        ],
        format=MovieRecommendation.model_json_schema()
    )
    
    result = MovieRecommendation.model_validate_json(response.message.content)  # type: ignore
    
    # podmień poster_path dla głównego filmu
    matched = movie_lookup.get(result.movie_title)
    if matched:
        result.poster_path = matched.get('poster_path', '')
        result.genres = matched.get('genre', [])
    
    # podmień poster_path dla extra_movies
    for extra in result.extra_movies:
        matched_extra = movie_lookup.get(extra.movie_title)
        if matched_extra:
            extra.poster_path = matched_extra.get('poster_path', '')
            extra.genres = matched_extra.get('genre', [])
    
    return result
    
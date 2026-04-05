from ollama import Client
from engine.prompts import AGENT_SYSTEM_PROMPT
from engine.vector import hybrid_search, reranker
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

async def decide(session, query, runtime: int, prompt: str, rating_weight: float = 0.25, limit_movies: int = 75):
    
    top_search = await hybrid_search(query, runtime, session, rating_weight, limit_movies)
    rerank = await reranker(prompt, top_search, limit_movies=20, batch_size=32)

    movie_lookup = {m['movie'].title: m['movie'] for m in rerank}

    movies_str = "\n".join([
        f"- {m['movie'].title} | "
        f"{', '.join(m['movie'].genre or [])} | "
        f"{', '.join(m['movie'].tags or [])} | "
        f"{m['movie'].description[:150]}"
        for m in rerank
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
        result.poster_path = matched.poster_path or ''
        result.genres = matched.genre or []
    for extra in result.extra_movies:
        matched_extra = movie_lookup.get(extra.movie_title)
        if matched_extra:
            extra.poster_path = matched_extra.poster_path or ''
            extra.genres = matched_extra.genre or []
    return result 
    
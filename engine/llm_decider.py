from ollama import AsyncClient
from engine.prompts import AGENT_SYSTEM_PROMPT
from engine.vector import hybrid_search, reranker
from pydantic import BaseModel
from typing import Optional
from datetime import date
import os
import time, random
import logging

logger = logging.getLogger(__name__)
client = AsyncClient(host=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

# ── Schematy dla LLM (tylko to co model może znać) ──────────────────────────

class LlmExtraMovie(BaseModel):
    """Schemat extra filmów zwracanych przez LLM — tylko tytuł i gatunki."""
    movie_title: str
    genres: list[str]

class LlmOutput(BaseModel):
    """Schemat odpowiedzi LLM — bez poster_path i release_date (LLM ich nie zna)."""
    thought: str
    movie_title: str
    reasoning_pl: str
    extra_movies: list[LlmExtraMovie]
    genres: list[str]

# ── Schematy odpowiedzi API (z danymi z bazy) ────────────────────────────────

class ExtraMovie(BaseModel):
    movie_title: str
    genres: list[str]
    poster_path: str
    release_date: Optional[date] = None   # mapowane z bazy po tytule
    runtime: Optional[int] = None
    rating: Optional[float] = None

class MovieRecommendation(BaseModel):
    thought: str
    movie_title: str
    reasoning_pl: str
    extra_movies: list[ExtraMovie]
    poster_path: str
    genres: list[str]
    release_date: Optional[date] = None   # mapowane z bazy po tytule
    runtime: Optional[int] = None
    rating: Optional[float] = None

async def decide(session, query, runtime: int, prompt: str, rating_weight: float = 0.25, limit_movies: int = 75):
    t1 = time.perf_counter()
    top_search = await hybrid_search(query, runtime, session, rating_weight, limit_movies)
    t2 = time.perf_counter()
    logger.info(f"hybrid serach took {t2-t1}")
    rerank = await reranker(prompt, top_search, limit_movies=20)
    t3 = time.perf_counter()
    logger.info(f"rerank took {t3-t2}")
    
    if not rerank:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Brak filmów spełniających kryteria, spróbuj np. zwiększyć maksymalny czas trwania.")
        

    random.shuffle(rerank)
    movie_lookup = {m['movie'].title: m['movie'] for m in rerank}
    # case-insensitive lookup — LLM często zwraca tytuł z inną wielkością liter
    movie_lookup_lower = {k.lower(): v for k, v in movie_lookup.items()}

    def find_movie(title: str):
        """Szuka filmu po tytule — najpierw exact, potem case-insensitive."""
        return movie_lookup.get(title) or movie_lookup_lower.get(title.lower())
    
    movies_str = "\n".join([
        f"- {m['movie'].title} | "
        f"{', '.join(m['movie'].genre or [])} | "
        f"{', '.join(m['movie'].tags or [])} | "
        f"{m['movie'].description[:150]}"
        for m in rerank
    ])
    user_prompt = f"""
    Candidates:
    {movies_str}

    Group preferences: {prompt}
    Output:
    """

    response = await client.chat(
        model="qwen2.5:3b",
        messages=[
            {'role': 'system', 
             'content': AGENT_SYSTEM_PROMPT},
            {'role': 'user', 
             'content': user_prompt}
        ],
        options={"temperature": 0.25, "top_p": 0.9},
        format=LlmOutput.model_json_schema()   # LLM dostaje schemat BEZ poster_path i release_date
    )
    
    llm_result = LlmOutput.model_validate_json(response.message.content)  # type: ignore
    t4 = time.perf_counter()
    logger.info(f"llm took {t4-t3}")

    # mapujemy dane z bazy (poster, rok, gatunki, czas trwania, ocena)
    matched = find_movie(llm_result.movie_title)
    result = MovieRecommendation(
        thought=llm_result.thought,
        movie_title=llm_result.movie_title,
        reasoning_pl=llm_result.reasoning_pl,
        extra_movies=[],
        poster_path=matched.poster_path or '' if matched else '',
        genres=matched.genre or [] if matched else llm_result.genres,
        release_date=matched.release_date if matched else None,
        runtime=matched.runtime if matched else None,
        rating=matched.rating if matched else None,
    )

    for extra in llm_result.extra_movies:
        matched_extra = find_movie(extra.movie_title)
        result.extra_movies.append(ExtraMovie(
            movie_title=extra.movie_title,
            genres=matched_extra.genre or [] if matched_extra else extra.genres,
            poster_path=matched_extra.poster_path or '' if matched_extra else '',
            release_date=matched_extra.release_date if matched_extra else None,
            runtime=matched_extra.runtime if matched_extra else None,
            rating=matched_extra.rating if matched_extra else None,
        ))

    return result

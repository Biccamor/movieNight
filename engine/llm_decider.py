from ollama import chat
from engine.prompts import AGENT_SYSTEM_PROMPT
from vector import hybrid_search
from pydantic import BaseModel
from enum import Enum


def decide(session, query, runtime: int, prompt: str,  rating_weight:float=0.25, limit_movies:int = 50):
    
    search = hybrid_search(query, runtime, session, rating_weight, limit_movies)
    movies_dict = {answer['movie']: answer['movie'] for answer in search}
    
    potential_movies = Enum('potential_movies', movies_dict)
    
    class Option(BaseModel):
        options_to_choose: potential_movies
    
    model = "gemma2:2b"

    response = chat(
        model=model,
        messages=[
            {'role': 'system', 
             'content': AGENT_SYSTEM_PROMPT},
            {'role': 'user', 
             'content': prompt}
                ],
            format = Option.model_json_schema()
        )
    
    return response.message.content
    
from database.database_setup import Movie
from sqlmodel import select
from flashrank import RerankRequest
import scripts.dependencies as d
import asyncio
def create_vector(prompt:list | str):
    
    embedding = d.model.encode(prompt, 
                            batch_size=20, 
                            max_length=512
                            )['dense_vecs']
    
    embedding_list = embedding.tolist() # type: ignore
    return embedding_list

async def reranker(prompt, top_movies: list, limit_movies:int = 25):

    passages = [
        {
            "id": i,
            "text": f"{m['movie'].title} | {', '.join(m['movie'].genre or [])} | {', '.join((m['movie'].tags or [])[:5])} | {m['movie'].description[:150]}"
        }
        for i, m in enumerate(top_movies)
    ]
    
    request = RerankRequest(query=prompt, passages=passages)
    results = await asyncio.to_thread(d.reranker.rerank, request)
    
    reranked = [top_movies[r["id"]] for r in results[:limit_movies]]
    return reranked

async def hybrid_search(query_vector: list[float],max_runtime: int, session,  rating_weight: float = 0.25, limit_movies: int = 50) -> list:
    

    rating_penalty = (10.0 - Movie.rating) / 10.0 
    # tym mniejszy hybrid_score tym lepiej, tym gorsza ocena tym dodatkowo "dalej" od idealnego filmu 0.0
    hybrid_score = (Movie.embedding.cosine_distance(query_vector) + (rating_weight * rating_penalty)).label("score") # type: ignore

    statement = (
        select(Movie, hybrid_score)
        .order_by(hybrid_score)
        .where(Movie.runtime <= max_runtime) # type: ignore #TODO: wymysl co jezeli runtime to none
        .limit(limit_movies)
    )
        
    return [
        {"movie": row[0], "score": float(row[1])}
        for row in session.exec(statement).all()
    ]
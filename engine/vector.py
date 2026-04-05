from database.database_setup import Movie
from sqlmodel import select
import scripts.dependencies as d
def create_vector(prompt:list | str):
    
    embedding = d.model.encode(prompt, 
                            batch_size=20, 
                            max_length=512
                            )['dense_vecs']
    
    embedding_list = embedding.tolist() # type: ignore
    return embedding_list

async def reranker(prompt, top_movies: list, limit_movies:int = 25, batch_size:int=32):

    def to_text(movie: Movie) -> str:
        genres = ", ".join(movie.genre or [])
        tags = ", ".join(movie.tags or [])
        return f"{movie.title} | {genres} | {tags} | {movie.description}"
    
    pairs = [(prompt, to_text(m["movie"])) for m in top_movies]
    scores = d.reranker.compute_score(pairs, batch_size=batch_size)
    if scores is None:
        return top_movies[:limit_movies]
    
    reranked = sorted(zip(top_movies, scores), key=lambda x: x[1], reverse=True)
    return [m for m, _ in reranked[:limit_movies]]

async def hybrid_search(query_vector: list[float],max_runtime: int, session,  rating_weight: float = 0.25, limit_movies: int = 5) -> list:
    

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
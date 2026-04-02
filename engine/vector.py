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

def hybrid_search(query_vector: list[float],max_runtime: int, session,  rating_weight: float = 0.25, limit_movies: int = 5):
    

    rating_penalty = (10.0 - Movie.rating) / 10.0 
    # tym mniejszy hybrid_score tym lepiej, tym gorsza ocena tym dodatkowo "dalej" od idealnego filmu 0.0
    hybrid_score = (Movie.embedding.cosine_distance(query_vector) + (rating_weight * rating_penalty)).label("score") # type: ignore

    statement = (
        select(Movie, hybrid_score)
        .order_by(hybrid_score)
        .where(Movie.runtime <= max_runtime) # type: ignore #TODO: wymysl co jezeli runtime to none
        .limit(limit_movies)
    )
    db_search = session.exec(statement).all()

    result =[]

    for row in db_search:
        #print(row)
        result.append({
            "movie": str(row[0]),
            "score":  float(row[1])
        })
    
    
    return result
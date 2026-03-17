from FlagEmbedding import BGEM3FlagModel
from database.main_db import engine
from database.database_setup import Movie
from sqlmodel import Session, select

model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

def create_vector(prompt:list | str):
    
    embedding = model.encode(prompt, 
                            batch_size=20, 
                            max_length=512
                            )['dense_vecs']
    
    embedding_list = embedding.tolist() # type: ignore
    return embedding_list

def hybrid_search(query_vector: list[float],max_runtime: int,  rating_weight: float = 0.25, limit_movies: int = 5):
    
    with Session(engine) as session:

        rating_penalty = (10.0 - Movie.rating) / 10.0
        # tym mniejszy hybrid_score tym lepiej, tym gorsza ocena tym dodatkowo "dalej" od idealnego filmu 0.0
        hybrid_score = (Movie.embedding.cosine_distance(query_vector) + (rating_weight * rating_penalty)).label("score") # type: ignore

        statement = (
            select(Movie, hybrid_score)
            .order_by(hybrid_score)
            .where(Movie.runtime <= max_runtime) # type: ignore #TODO: wymysl co jezeli runtime to none
            .limit(limit_movies)
        )
        
        return session.exec(statement).all()

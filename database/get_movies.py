import requests
from dotenv import dotenv_values
from sqlmodel import Session
from database.main_db import engine
from engine.vector import create_vector, model
from database.database_setup import Movie
import time
import concurrent.futures
from requests.exceptions import RequestException
from sqlalchemy.dialects.postgresql import insert
from datetime import date
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0MjQ3ZWUxM2E4NDg4NzQ4YjhjOWYwYjJiY2E3NzI2NCIsIm5iZiI6MTc3MjkwNzI5Ny4wNjA5OTk5LCJzdWIiOiI2OWFjNmIyMWIzYWU1Y2U0YTU3MTcxNDkiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.oywsdyuQ0pYl8w4O7d6ouRKOFrWCXwc1o3BOYNTYUJY"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}
PAGES = 100
TMDB_API = "4247ee13a8488748b8c9f0b2bca77264"
http = requests.Session()
http.headers.update(headers)

def fetch_details(movie):
    """Pomocnicza funkcja do pobierania detali jednego filmu"""
    movie_url = f"https://api.themoviedb.org/3/movie/{movie['id']}?append_to_response=keywords"
    try:
        response = http.get(movie_url, timeout=10) 
        
        if response.status_code == 429:
            print(f"Rate limit (429) dla {movie['id']}.")
            time.sleep(2)
            return fetch_details(movie)
            
        return response.json()

    except (RequestException, Exception) as e:
        print(f" Błąd sieci dla filmu {movie['id']}: {e}.")
        time.sleep(3)
        return fetch_details(movie) 
    

def create_movie_prompt(genres: list, movie_title: str, desc: str, keywords: list):
    genres_str = ", ".join(genres)
    keywords_str = ", ".join(keywords)

    prompt = f"movie title is {movie_title}, the genres are {genres_str}, and the description overview is {desc}. the words that describe movie {keywords_str}"

    return prompt

def get_genres() -> dict[str, str]:
    """
    Function to generate dict of genres that tmbd have based on url 
    """
    url_genres = "https://api.themoviedb.org/3/genre/movie/list?language=en"
    response = requests.get(url_genres, headers=headers).json()["genres"]
    genres_dict = {}
    for genre in response:
        genres_dict.update({genre['id']:  genre['name']})
    return genres_dict

def add_movies():
    genre_dict = get_genres()

    with Session(engine) as session:
        movie_batch = []
        for page in range(43, PAGES+1): 
            print(f"CURRENT PAGE: {page}")
            url = f"https://api.themoviedb.org/3/movie/popular?language=en-US&page={page}"
            response = http.get(url).json()
            movies_list = response["results"]

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                all_details = list(executor.map(fetch_details, movies_list))

            page_prompts = []
            page_movies_data = []

            for i, detail_res in enumerate(all_details):
                movie = movies_list[i]
                runtime = detail_res.get("runtime", 0)
                keywords_list = [k["name"] for k in detail_res.get("keywords", {}).get("keywords", [])]
                genres_names = [genre_dict[g_id] for g_id in movie['genre_ids']]
                
                prompt = create_movie_prompt(genres_names, movie['title'], movie['overview'], keywords=keywords_list)
                
                page_prompts.append(prompt)
                page_movies_data.append({
                    "movie": movie, "runtime": runtime, "keywords": keywords_list, "genres": genres_names
                })

            embeddings = create_vector(page_prompts)

            for i, data in enumerate(page_movies_data):
                m = data["movie"]
                movie_batch.append(Movie(
                    tmdb_id=m['id'], title=m['title'], description=m['overview'],
                    genre=data["genres"], release_date=date.fromisoformat(m['release_date'])  if m['release_date'] else None , rating=m['vote_average'],
                    embedding=embeddings[i], runtime=data["runtime"], tags=data["keywords"],
                    poster_path=m['poster_path']
                ))

            if page % 3 == 0 or page == PAGES: 
                try: 
                    for movie_obj in movie_batch:
                        # Zamieniamy obiekt na słownik danych
                        data = movie_obj.model_dump(exclude={"movie_id"})
                        
                        stmt = insert(Movie).values(data).on_conflict_do_nothing(index_elements=['tmdb_id'])
                        session.exec(stmt)
                    
                    session.commit()
                    print(f"BATCH SAVED up to page {page}")
                    movie_batch = []
                except Exception as e:
                    session.rollback()
                    print(f"ERROR during commit: {e}")
                    movie_batch = []

add_movies()
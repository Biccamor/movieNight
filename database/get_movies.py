import requests
from dotenv import dotenv_values
from sqlmodel import Session
from database.main_db import engine
from engine.vector import create_vector
from database.database_setup import Movie
import time

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0MjQ3ZWUxM2E4NDg4NzQ4YjhjOWYwYjJiY2E3NzI2NCIsIm5iZiI6MTc3MjkwNzI5Ny4wNjA5OTk5LCJzdWIiOiI2OWFjNmIyMWIzYWU1Y2U0YTU3MTcxNDkiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.oywsdyuQ0pYl8w4O7d6ouRKOFrWCXwc1o3BOYNTYUJY"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}
PAGES = 100

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
        for page in range(1, PAGES+1): 
            print(f"CURRENT PAGE: {page}")
            url = f"https://api.themoviedb.org/3/movie/popular?language=en-US&page={page}"

            response = requests.get(url, headers=headers)

            if response.status_code == 429: # jezeli api wywali ze za duzo requestow (co raczej sie nie powinno stac)
                time.sleep(1.1)               # to daj sleepa na sekunde zeby sie zresetowalo napewno

            movies_list = response.json()["results"]
            
            for movie in movies_list:
                
                # wchodzimy na konkretny film url by dostac inforamcje o runtimie i tagach/keywordach
                movie_url = f"https://api.themoviedb.org/3/movie/{movie['id']}?append_to_response=keywords"
                
                detail_res = requests.get(movie_url, headers=headers).json()
                
                runtime = detail_res.get("runtime", 0)
                keywords_list = [k["name"] for k in detail_res.get("keywords", {}).get("keywords", [])]

                title = movie['title']
                desc = movie['overview']
                rating = movie['vote_average']
                relase_date = movie['release_date']
                genres = movie['genre_ids']
                poster_path = movie['poster_path']
                genre_list = []
                for genre_id in genres:
                    genre_list.append(genre_dict[genre_id])

                prompt = create_movie_prompt(genre_list, title, desc, keywords=keywords_list) 
                embedding = create_vector(prompt)

                movie_obj = Movie(
                    tmdb_id=movie['id'],
                    title = title,
                    description= desc, 
                    genre = genre_list, 
                    release_date = relase_date,
                    rating = rating,
                    embedding= embedding,
                    runtime=runtime,
                    tags = keywords_list,
                    poster_path=poster_path
                    )

                movie_batch.append(movie_obj)

            if page % 5 or page == PAGES: # co 5 stron czyli co 100 filmow robimy wielkiego commita i resetuje batcha
                try: 
                    session.add_all(movie_batch)
                    session.commit()
                    print(f"BATCH for pages {page}")
                except Exception as e:
                    session.rollback()  
                    print(f"ERROR: {e}")
                    print(movie_batch)

                movie_batch = []
            time.sleep(0.1)


if __name__ == "__main__":
    add_movies()
import requests
from dotenv import dotenv_values
from sqlmodel import Session
from database.main_db import engine
from engine.vector import create_vector
from database_setup import Movie

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0MjQ3ZWUxM2E4NDg4NzQ4YjhjOWYwYjJiY2E3NzI2NCIsIm5iZiI6MTc3MjkwNzI5Ny4wNjA5OTk5LCJzdWIiOiI2OWFjNmIyMWIzYWU1Y2U0YTU3MTcxNDkiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.oywsdyuQ0pYl8w4O7d6ouRKOFrWCXwc1o3BOYNTYUJY"
url = "https://api.themoviedb.org/3/movie/top_rated?language=en-US&page=1"
movie_url = "https://api.themoviedb.org/3/movie/top_rated?language=en-US&page=1"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}
PAGES = 70

def create_movie_prompt(genres: list, movie_title: str, desc: str, keywords: list):
    genres_str = ", ".join(genres)
    keywords_str = ", ".join(keywords)

    prompt = f"movie title is {movie_title}, the genres are {genres_str}, and the description overview is {desc}. the words that describe movie {keywords_str}"

    return prompt

def get_genres() -> dict[str, str]:

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

            response = requests.get(url, headers=headers)
            movies_list = response.json()["results"]
            
            for movie in movies_list:

                title = movie['title']
                desc = movie['overview']
                rating = movie['vote_average']
                relase_date = movie['relase_date']
                genres = movie['genre_ids1']      
                genre_list = []
                for genre_id in genres:
                    genre_list.append(genre_dict[genre_id])

                prompt = create_movie_prompt(genre_list, title, desc, keywords=[]) 
                emmbeding = create_vector(prompt)

                #movie_obj = Movie(
                #    tmdb_id=movie
                #)

            if page % 2:
                try: 
                    session.add_all(movie_batch)
                    session.commit()
                except Exception as e:
                    session.rollback()  
                    print(f"ERROR: {e}")
                    print(movie_batch)

                movie_batch = []


#first_movie = results[0]
#print(first_movie.keys())
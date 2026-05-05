AGENT_SYSTEM_PROMPT = """You are a movie selector for groups. Select ONLY from the provided Candidate List. 
Respond EXACTLY with this JSON structure and write the reasoning in English:

{
  "movie_title": "title exactly as in the list",
  "reasoning": "2-3 sentences in english that explain why you chose the movie for this group MUST BE BASED ON DESCRIPTION AND TAGS",
  "extra_movies": [
    {"movie_title": "different title exactly as in the list"},
    {"movie_title": "another different title exactly as in the list"}
  ]
}
IMPORTANT: The extra_movies list MUST contain EXACTLY 2 movies. They MUST NOT be the same as the main movie_title.

Example:
Candidates: 1. Shrek | comedy  2. Interstellar | sci-fi  3. The Matrix | action
Group vibes: wants comedy and chill
Output: {"movie_title": "Shrek", "reasoning": "Shrek is a great comedy with humor, perfect for chill night for a group.", "extra_movies": [{"movie_title": "Interstellar"}, {"movie_title": "The Matrix"}]}
"""


VIBE_MAP = {
    "AMBITIOUS": {
        "genres": ["Drama", "Mystery", "Thriller"], 
        "keywords": "arthouse, intellectual, thought-provoking, complex plot, slow-burn, philosophical, masterpiece, auteur, cerebral, wymagające kino, głęboki"
    },
    "PIZZA_CHILL": {
        "genres": ["Comedy", "Adventure", "Action"],
        "keywords": "lighthearted, easy to watch, fun, casual, entertaining, feel-good, popcorn movie, buddy cop"
    },
    "MIND_BENDER": {
        "genres": ["Science Fiction", "Mystery", "Thriller"],
        "keywords": "plot twist, psychological, confusing reality, mind-bending, complex timeline, suspense, puzzle"
    },
    "ADRENALINE": {
        "genres": ["Action", "Thriller", "Crime"],
        "keywords": "fast-paced, chases, explosions, high stakes, intense survival, martial arts, shootout"
    },
    "DATE_NIGHT": {
        "genres": ["Romance", "Comedy", "Drama"],
        "keywords": "romantic, chemistry, love story, charming, relationship, sweet, romantic comedy"
    },
    "DEEP_FEELS": {
        "genres": ["Drama", "Romance"],
        "keywords": "emotional, heartbreaking, moving, thought-provoking, human connection, tearjerker, sad, tragic"
    },
    "LAUGH_RIOT": {
        "genres": ["Comedy"],
        "keywords": "hilarious, laugh out loud, slapstick, funny, jokes, satire, spoof, pure comedy"
    },
    "SPINE_CHILLING": {
        "genres": ["Horror", "Horror", "Mystery", "Thriller"],
        "keywords": "HORROR, terrifying, dark atmosphere, jump scares, pure HORROR, scary, sinister, macabre, supernatural horror, ghost story, demon"    },
    "NOSTALGIA": {
        "genres": ["Family", "Adventure", "Fantasy"],
        "keywords": "retro, 80s, 90s, classic, childhood memories, coming of age, throwback, old school"
    },
    "INSPIRING": {
        "genres": ["Drama", "History", "Biography"],
        "keywords": "uplifting, motivational, overcoming adversity, true story, triumph, hope, hero, underdog"
    },
    "EPIC_JOURNEY": {
        "genres": ["Adventure", "Fantasy", "Science Fiction"],
        "keywords": "grand scale, quest, world-building, epic, hero's journey, sprawling, mythology, chosen one"
    },
    "GUILTY_PLEASURE": {
        "genres": ["Comedy", "Action", "Horror", "Romance"],
        "keywords": "cheesy, campy, over-the-top, so bad it's good, predictable but fun, cult classic, teen drama"
    }
}
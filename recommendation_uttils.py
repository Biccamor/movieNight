from schemas import User
import numpy as np

def create_prompt(data_preferences: User, meeting_type: str) -> str:
    AGENT_SYSTEM_PROMPT = ""

    for user in data_preferences:
        
        likes = ", ".join(user.preferences.genre_likes if user.preferences.genre_likes != [] else "all")
        dislikes = ", ".join(user.preferences.genre_dislike if user.preferences.genre_dislike != [] else "none")
        time_limit = user.preferences.time

        user_prompt = f"user: {user.user_name} likes genres {likes} and dislikes genres {dislikes} would prefer movie  maximum with length {time_limit}"
        AGENT_SYSTEM_PROMPT += user_prompt
    
    AGENT_SYSTEM_PROMPT += f"users are having a meeting that is {meeting_type}"

    return AGENT_SYSTEM_PROMPT

def calculate_recommended_time(users: list[User]) -> tuple[int, int]:
    
    times = [u.preferences.time for u in users]

    if not times: 
        return(90,120)

    min_time = min(times)
    mean_time = np.mean(times)
    recommended_time = int(np.floor((float(min_time)+mean_time)/2))

    return (recommended_time, min_time)
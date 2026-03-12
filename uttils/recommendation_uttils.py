from schemas import SessionUser
import numpy as np

def create_prompt(data_preferences: SessionUser, meeting_type: str) -> str:
    AGENT_SYSTEM_PROMPT = ""

    for user in data_preferences:
        
        vibes = ", ".join(user.preferences.vibes if user.preferences.vibes != [] else "all")
        hard_nos = ", ".join(user.preferences.hard_nos if user.preferences.hard_nos != [] else "none")
        time_limit = user.preferences.max_runtime

        user_prompt = f"user: {user.user_name} wants vibes {vibes} and DEFINETLY DOESNT WANT {hard_nos} "
        AGENT_SYSTEM_PROMPT += user_prompt
    
    AGENT_SYSTEM_PROMPT += f"users are having a meeting that is {meeting_type}"

    return AGENT_SYSTEM_PROMPT

def calculate_recommended_time(users: list[SessionUser]) -> tuple[int, int]:
    
    times = [u.preferences.max_runtime for u in users]

    if not times: 
        return(90,120)

    min_time = min(times)
    mean_time = np.mean(times)
    recommended_time = int(np.floor((float(min_time)+mean_time)/2))

    return (recommended_time, min_time)
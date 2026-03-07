from fastapi import APIRouter
from engine.llm_engine import llm_response
from schemas import Data

app = APIRouter(prefix="/recommendation", tags=["reccomendation"])

def create_prompt(data_preferences: list[dict], meeting_type) -> str:
    AGENT_SYSTEM_PROMPT = ""

    for user in data_preferences:
        
        user_likes = ", ".join(user.preferences.genre_like if user.preferences.genre_likes != [] else "all")
        user_dislike = ", ".join(user.preferences.genre_dislike if user.preferences.genre_dislike != [] else "none")
        time_limit = "minuts, ".join(str(user.preferences.time) if user.preferences.time != [] else "doesn't matter")

        user_prompt = f"user: {user.user_name} likes genres {user_likes} and dislikes genres {user_dislike} would prefer movie with length {time_limit}"
        AGENT_SYSTEM_PROMPT += user_prompt
    
    AGENT_SYSTEM_PROMPT += f"users are having a meeting that is {meeting_type}"

    return AGENT_SYSTEM_PROMPT


@app.post("/{group_id}")
async def recommendation(meta_data: Data) -> dict:

    user_list = meta_data.users
    meeting_type = meta_data.meeting

    AGENT_USER_PROMPT = create_prompt(data_preferences=user_list, meeting_type=meeting_type)
    
    respone = await llm_response(AGENT_USER_PROMPT)

    return{
        "group_id": meta_data.id,
        "response": respone
    }
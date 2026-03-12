from fastapi import APIRouter, Depends
from engine.llm_engine import llm_response
from schemas import Data
from database.database_setup import Session
from database.main_db import get_session
from uuid import uuid4
from recommendation_uttils import create_prompt, calculate_recommended_time

router = APIRouter(prefix="/recommendation", tags=["reccomendation"])

@router.post("/{group_id}")
async def get_recommendation(meta_data: Data, session=Depends(get_session)) -> dict:

    user_list = meta_data.users
    meeting_type = meta_data.meeting

    users_seen = {
        str(u.user_id): {
            "allow_seen": u.preferences.allow_seen,
            "user_name": u.user_name
        } for u in user_list
    }
    recommended_time, min_time = calculate_recommended_time(user_list)
    user_id_list = [u.user_id for u in user_list]
    preferences_excluded = [
        u.model_dump(exclude={"preferences": {"time", "allow_seen"}}) 
        for u in user_list
    ]

    new_group = Session(session_id=uuid4(), 
                          recommended_runtime=recommended_time,
                          min_runtime=min_time,
                          occasion=meeting_type,
                          allow_seen= users_seen,
                          preferences=preferences_excluded,
                          users_in_session=user_id_list)

    session.add(new_group)
    session.commit()

    AGENT_USER_PROMPT = create_prompt(data_preferences=user_list, meeting_type=meeting_type)
    
    respone = await llm_response(AGENT_USER_PROMPT)

    return{
        "group_id": meta_data.id,
        "response": respone
    }
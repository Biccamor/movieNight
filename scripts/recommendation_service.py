from fastapi import Depends
from schemas import MovieSession
from database.database_setup import Session
from database.main_db import get_session
from uuid import uuid4
from schemas import SessionUser
import numpy as np
from engine.vector import create_vector, get_recoms

class RecomService:
    
    def __init__(self, meta_data: MovieSession, session = Depends(get_session())):
        self.session = session
        self.meta_data = meta_data
        self.meeting_type = self.meta_data.meeting_type
        self.user_list = self.meta_data.users

    def add_db(self):
        
        users_seen = {
            str(u.user_id): {
                "allow_seen": u.preferences.allow_seen,
                "user_name": u.user_name
            } for u in self.user_list
        }
        recommended_time, min_time = RecomService.get_time(self.user_list)
        user_id_list = [u.user_id for u in self.user_list]
        preferences_excluded = [
            u.model_dump(exclude={"preferences": {"time", "allow_seen"}}) 
            for u in self.user_list
        ]

        AGENT_USER_PROMPT = self.create_prompt()
        self.vector = create_vector(AGENT_USER_PROMPT)
        new_group = Session(session_id=uuid4(), 
                            recommended_runtime=recommended_time,
                            min_runtime=min_time,
                            occasion=self.meeting_type,
                            allow_seen= users_seen,
                            preferences=preferences_excluded,
                            users_in_session=user_id_list,
                            embedding_preferences=self.vector)

        self.session.add(new_group)
        self.session.commit()


    def create_prompt(self) -> str:

        AGENT_SYSTEM_PROMPT = ""
        data_preferences = self.user_list

        for user in data_preferences:
            
            vibes = ", ".join(user.personal_vibe.vibes if user.personal_vibe.vibes != [] else "all")
            hard_nos = ", ".join(user.personal_vibe.hard_nos if user.personal_vibe.hard_nos != [] else "none")
            time_limit = user.personal_vibe.max_runtime

            user_prompt = f"user: {user.user_name} wants vibes {vibes} and DEFINETLY DOESNT WANT {hard_nos} "
            AGENT_SYSTEM_PROMPT += user_prompt
        
        AGENT_SYSTEM_PROMPT += f"users are having a meeting that is {self.meeting_type}"

        return AGENT_SYSTEM_PROMPT
    
    def get_time(self) -> tuple[int, int]:
    
        times = [u.preferences.max_runtime for u in self.user_list]

        if not times: 
            return(90,120)

        min_time = min(times)
        mean_time = np.mean(times)
        recommended_time = int(np.floor((float(min_time)+mean_time)/2))

        return (recommended_time, min_time)
    
    def _main(self):
        
        recoms = get_recoms(self.vector)

        return recoms 
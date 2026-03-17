from fastapi import Depends
from schemas import MovieSession
from database.database_setup import Room_Session
from database.main_db import get_session
from uuid import uuid4
import numpy as np
from engine.vector import create_vector, hybrid_search

class RecomService:
    
    def __init__(self, meta_data: MovieSession, session):
        self.session = session
        self.meta_data = meta_data
        self.meeting_type = self.meta_data.meeting_type
        self.user_list = self.meta_data.users
        self.preferences = self.meta_data.final_preferences

    def _add_db(self):
        
        users_seen = {
            str(u.user_id): {
                "allow_seen": u.personal_vibe.allow_seen,
                "user_name": u.user_name
            } for u in self.user_list
        }
        self.recommended_time, self.min_time = self.get_time()
        user_id_list = [u.user_id for u in self.user_list]
        preferences_excluded = [
            u.model_dump(exclude={"preferences": {"time", "allow_seen"}}) 
            for u in self.user_list
        ]

        AGENT_USER_PROMPT = self.create_prompt()
        self.vector = create_vector(AGENT_USER_PROMPT)
        new_group = Room_Session(session_id=uuid4(), 
                            recomended_runtime=self.recommended_time,
                            min_runtime=self.min_time,
                            occasion=self.meeting_type,
                            allow_seen=users_seen,
                            preferences=preferences_excluded,
                            users_in_session=user_id_list,
                            embedding_preferences=self.vector)

        self.session.add(new_group)
        self.session.commit()


    def _create_prompt(self) -> str:

        AGENT_SYSTEM_PROMPT = ""
        data_preferences = self.user_list

        for user in data_preferences:
            
            vibes = ", ".join(user.personal_vibe.vibes if user.personal_vibe.vibes != [] else "all")
            hard_nos = ", ".join(user.personal_vibe.hard_nos if user.personal_vibe.hard_nos != [] else "none")

            user_prompt = f"user: {user.user_name} wants vibes {vibes} and DEFINETLY DOESNT WANT {hard_nos} "
            AGENT_SYSTEM_PROMPT += user_prompt
        
        AGENT_SYSTEM_PROMPT += f"users are having a meeting that is {self.meeting_type}"

        return AGENT_SYSTEM_PROMPT
    
    def _get_time(self) -> tuple[int, int]:
        """
        returns the recommended time by algorthim and the time that is the smallest from users preferences
        """

        times = [u.personal_vibe.max_runtime for u in self.user_list]

        if not times: 
            return(120, 90)

        min_time = min(times)
        mean_time = np.mean(times)
        recommended_time = int(np.floor((float(min_time)+mean_time)/2))

        return (recommended_time, min_time)
    
    def _main(self):
        
        recoms = hybrid_search(self.vector, max(self.recommended_time, self.min_time),
                               rating_weight=0.25, limit_movies=5)

        return recoms 
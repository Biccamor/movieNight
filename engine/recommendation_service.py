from schemas.schemas import MovieSession
from database.database_setup import Room_Session
from uuid import uuid4, UUID
import numpy as np
from engine.vector import create_vector, hybrid_search
from engine.llm_decider import decide


class RecomService:

    def __init__(self, meta_data: MovieSession, session):
        self.session = session
        self.meta_data = meta_data
        self.meeting_type = self.meta_data.meeting_type
        self.user_list = self.meta_data.users
        self.preferences = self.meta_data.final_preferences

    def _add_db(self) -> UUID:
        """
        Zapisuje sesję do bazy danych i zwraca session_id.
        Nie wywołuje AI – jest szybki.
        """
        users_seen = {
            str(u.user_id): {
                "allow_seen": u.personal_vibe.allow_seen,
                "user_name": u.user_name
            } for u in self.user_list
        }
        recommended_time, min_time = self._get_time()
        user_id_list = [str(u.user_id) for u in self.user_list]
        preferences_excluded = [
            u.model_dump(exclude={"preferences": {"time", "allow_seen"}}, mode='json')
            for u in self.user_list
        ]

        agent_prompt = self._create_prompt()
        vector = create_vector(agent_prompt)

        session_id = uuid4()
        new_group = Room_Session(
            session_id=session_id,
            recomended_runtime=recommended_time,
            min_runtime=min_time,
            occasion=self.meeting_type,
            allow_seen=users_seen,
            preferences=preferences_excluded,
            users_in_session=user_id_list,
            embedding_preferences=vector,
        )

        self.session.add(new_group)
        self.session.commit()

        return session_id

    def _create_prompt(self) -> str:
        prompt = ""
        for user in self.user_list:
            vibes = ", ".join(user.personal_vibe.vibes if user.personal_vibe.vibes != [] else "all")
            prompt += f"user: {user.user_name} wants movies with vibes: {vibes}"
        prompt += f"users are having a meeting that is {self.meeting_type}"
        return prompt

    def _get_time(self) -> tuple[int, int]:
        """
        Zwraca (recommended_time, min_time) na podstawie preferencji użytkowników.
        """
        times = [u.personal_vibe.max_runtime for u in self.user_list]
        if not times:
            return (120, 90)
        min_time = min(times)
        mean_time = np.mean(times)
        recommended_time = int(np.floor((float(min_time) + mean_time) / 2))
        return (recommended_time, min_time)

    @staticmethod
    async def get_recommendations_from_db(db_session: Room_Session, session):
        """
        Pobiera rekomendacje filmów na podstawie danych już zapisanej sesji w bazie.
        Wywołuje model AI – może być wolny.
        """
        vector = db_session.embedding_preferences
        max_runtime = max(db_session.recomended_runtime or 120, db_session.min_runtime or 90)

        users_info = " ".join(
            f"user {u.get('user_name', 'unknown')} prefers vibes: {', '.join(u.get('personal_vibe', {}).get('vibes', []))}"
            for u in (db_session.preferences or [])
        )
        agent_prompt = f"Recommend a movie for a group of users containing: {users_info}"

        recommendations = await decide(session, vector, max_runtime, agent_prompt)
        return recommendations
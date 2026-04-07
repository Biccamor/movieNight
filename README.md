# 🎬 MovieNight — Backend API

**MovieNight** is an AI-powered group movie recommendation engine. It helps groups of people — friends, couples, families, or anyone watching together — find the perfect movie to watch based on everyone's personal taste, vibe preferences, and time constraints.

The backend is built with **FastAPI**, uses **PostgreSQL + pgvector** for semantic search, and leverages **Ollama** with local LLMs for intelligent recommendation decisions.

---

## ✨ Features

- 🤝 **Group-aware recommendations** — merges preferences from multiple users into a single movie session
- 🧠 **AI-powered decisions** — uses a local LLM (via Ollama) to select the best movies for the group
- 🔍 **Semantic + hybrid search** — vector embeddings (1024-dim) on movies and user preferences via pgvector
- 👤 **User authentication** — JWT-based auth with Argon2 password hashing
- 🎭 **Vibe system** — users express mood via vibes (e.g. `PIZZA_CHILL`, `DATE_NIGHT`, `MIND_BENDER`)
- ⏱️ **Runtime matching** — automatically calculates the optimal movie length for the whole group
- 🚫 **Hard exclusions** — users can block content like gore, sad endings, or slow burns
- 🗓️ **Era filtering** — filter movies by decade (80s, 90s, 2000s, etc.)

---

## 🏗️ Tech Stack

| Layer           | Technology                              |
|-----------------|-----------------------------------------|
| Framework       | FastAPI                                 |
| Language        | Python 3.11                             |
| Database        | PostgreSQL 17 + pgvector                |
| ORM             | SQLModel + SQLAlchemy                   |
| AI / LLM        | Ollama (local)                          |
| Embeddings      | `FlagEmbedding`, `sentence-transformers`|
| Auth            | JWT (PyJWT) + Argon2 password hashing   |
| Containerization| Docker + Docker Compose                 |

---

## 📁 Project Structure

```
movieNight/
├── main.py                  # FastAPI app entry point, lifespan, middleware
├── compose.yaml             # Docker Compose (app + PostgreSQL + Ollama)
├── DockerFile               # App container definition
├── requirements.txt         # Python dependencies
│
├── routers/                 # API route handlers
│   ├── auth_router.py       # /auth — register & login
│   ├── recommendation_router.py  # /recommendation — get movie recommendations
│   ├── metadata_router.py   # /metadata — preference options (vibes, eras)
│   └── preference_router.py    # /preferences — save preferences
│
├── engine/                  # Core AI recommendation logic
│   ├── recommendation_service.py  # Orchestrates the full recommendation flow
│   ├── vector.py            # Vector creation & hybrid search
│   ├── llm_decider.py       # LLM-powered final movie selection
│   └── prompts.py           # Prompt templates
│
├── database/                # Database layer
│   ├── main_db.py           # Engine setup, session management, table creation
│   ├── database_setup.py    # SQLModel table definitions
│   ├── get_movies.py        # Movie data ingestion utilities
│   └── delete_db.py        # DB cleanup utilities
│
├── schemas/
│   └── schemas.py           # Pydantic request/response models & settings
│
└── scripts/                 # Utility scripts
    ├── dependencies.py      # Startup: model & DB loading
    └── security.py          # Password hashing & JWT signing
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Ollama](https://ollama.com/) (or let the compose file handle it)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/movieNight.git
cd movieNight
```

### 2. Configure environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://my_user:my_pwd@db:5432/my_db
OLLAMA_BASE_URL=http://ollama:11434
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE=25
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

This will start:
- **PostgreSQL 17** with pgvector on port `5433`
- **Ollama** on port `11434`
- **MovieNight API** on port `8010`

### 4. Access the API

- API Base URL: `http://localhost:8010`
- Interactive Docs: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

---

## 📡 API Endpoints

### Auth — `/auth`

| Method | Endpoint          | Description              |
|--------|-------------------|--------------------------|
| POST   | `/auth/register`  | Create a new user account |
| POST   | `/auth/login`     | Login and receive a JWT token |

### Preferences — `/preferences`

| Method | Endpoint          | Description              |
|--------|-------------------|--------------------------|
| POST   | `/preferences/save` | Save user preferences |

### Recommendations — `/recommendation`

| Method | Endpoint           | Description                                    |
|--------|--------------------|------------------------------------------------|
| POST   | `/recommendation/` | Get AI-powered movie recommendations for a group session |

**Request body example:**
```json
{
  "invite_code": "XJ79B",
  "meeting_type": "EKIPA",
  "users": [
    {
      "user_id": "uuid-here",
      "user_name": "Alice",
      "personal_vibe": {
        "vibes": ["LAUGH_RIOT", "PIZZA_CHILL"],
        "hard_nos": ["GORE"],
        "max_runtime": 120,
        "allow_seen": false,
        "eras": ["Lata 90.", "Lata 00."]
      }
    }
  ]
}
```

### Metadata — `/metadata`

| Method | Endpoint                       | Description                               |
|--------|--------------------------------|-------------------------------------------|
| GET    | `/metadata/preferences-options` | Returns available vibes and movie eras   |

---

## 🧠 Recommendation Engine

The recommendation pipeline works in six steps:

1. **Preference aggregation** — Collects all users' vibes and runtime constraints
2. **Prompt construction** — Builds a natural-language prompt summarizing the group's mood
3. **Vector embedding** — Encodes the prompt into a 1024-dimensional vector using `FlagEmbedding`
4. **Hybrid search** — Uses pgvector to find the best matching movies from the database via hybrid (vector + metadata) search
5. **Reranker** — Uses `FlagEmbedding` to rerank the movies based on the prompt
6. **LLM decision** — Uses Ollama to rank and select the best matching movies from the database via hybrid (vector + metadata) search

---

## 🗃️ Database Models

| Table          | Description                                           |
|----------------|-------------------------------------------------------|
| `app_user`     | User accounts with email, hashed password, taste vector |
| `movie`        | Movie catalogue with metadata and semantic embeddings |
| `room_session` | Group session tracking with aggregated preferences    |
| `rating`       | Per-user movie ratings (`-1` dislike, `0` seen, `1` like) |

---

## 🔐 Security

- Passwords are hashed using **Argon2** (winner of the Password Hashing Competition)
- Authentication tokens are **JWT** with configurable expiration
- Non-root Docker container (`appuser`) for runtime security

---

## 📄 License

This project is proprietary software. See [LICENSE.md](./LICENSE.md) for details.  
© 2026 Fabian. All rights reserved.

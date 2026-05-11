"""
Migracja embeddingów: BGE-M3 (1024-dim) → bge-base-en-v1.5 (768-dim)

Co robi:
  1. Zmienia kolumnę movie.embedding z Vector(1024) na Vector(768)
  2. Zmienia kolumnę room_session.embedding_preferences z Vector(1024) na Vector(768)
  3. Zmienia kolumnę app_user.user_taste z Vector(1024) na Vector(768)
  4. Dropuje stary HNSW index i tworzy nowy po migracji
  5. Re-embeduje WSZYSTKIE filmy nowym modelem (bge-base-en-v1.5)

Użycie:
    python scripts/migrate_embeddings.py

Wymagania:
    - PostgreSQL musi działać (docker compose up db)
    - pip install sentence-transformers sqlmodel psycopg2-binary
    - Uruchamiac LOKALNIE (nie w Dockerze) — łączy się przez DATABASE_URL_LOCAL
"""

import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from sqlmodel import Session, create_engine, select, text
from sentence_transformers import SentenceTransformer
from database.database_setup import Movie

# ── Konfiguracja ─────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL_LOCAL")
if not DATABASE_URL:
    print("❌ Brak DATABASE_URL_LOCAL w .env")
    sys.exit(1)

MODEL_NAME = "BAAI/bge-base-en-v1.5"
NEW_DIM = 768
BATCH_SIZE = 64  # ile filmów embedować naraz

engine = create_engine(DATABASE_URL, echo=False)

# ── Krok 1: Załaduj model ───────────────────────────────────────────

print(f"\n{'='*60}")
print(f"  MIGRACJA EMBEDDINGÓW → {MODEL_NAME} ({NEW_DIM}-dim)")
print(f"{'='*60}\n")

print(f"⏳ Ładuję model {MODEL_NAME}...")
t0 = time.perf_counter()
model = SentenceTransformer(MODEL_NAME)
print(f"✅ Model załadowany ({time.perf_counter() - t0:.1f}s)\n")

# ── Krok 2: Migracja kolumn w PostgreSQL ─────────────────────────────

print("⏳ Migracja kolumn wektorowych...")

ALTER_STATEMENTS = [
    # Dropnij stary HNSW index (zależny od starego wymiaru)
    "DROP INDEX IF EXISTS hnsw_movie;",

    # Zmień wymiar kolumn
    f"ALTER TABLE movie ALTER COLUMN embedding TYPE vector({NEW_DIM}) USING NULL;",
    f"ALTER TABLE room_session ALTER COLUMN embedding_preferences TYPE vector({NEW_DIM}) USING NULL;",
    f"ALTER TABLE app_user ALTER COLUMN user_taste TYPE vector({NEW_DIM}) USING NULL;",
]

with Session(engine) as session:
    for stmt in ALTER_STATEMENTS:
        try:
            session.exec(text(stmt))  # type: ignore
            print(f"  ✅ {stmt[:70]}...")
        except Exception as e:
            print(f"  ⚠️  {stmt[:50]}... — {e}")
            session.rollback()
    session.commit()

print("✅ Kolumny zmienione\n")

# ── Krok 3: Re-embedding filmów ─────────────────────────────────────

def create_movie_prompt(movie: Movie) -> str:
    """Tworzy prompt embeddingowy dla filmu (taki sam jak w get_movies.py)."""
    genres_str = ", ".join(movie.genre or [])
    keywords_str = ", ".join(movie.tags or [])
    desc = movie.description or ""
    return (
        f"movie title is {movie.title}, the genres are {genres_str}, "
        f"and the description overview is {desc}. "
        f"the words that describe movie {keywords_str}"
    )


with Session(engine) as session:
    # Policz filmy
    all_movies = session.exec(select(Movie)).all()
    total = len(all_movies)
    print(f"📊 Filmów w bazie: {total}")
    print(f"⏳ Re-embedding w batchach po {BATCH_SIZE}...\n")

    t_start = time.perf_counter()
    updated = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch = all_movies[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        # Generuj prompty
        prompts = [create_movie_prompt(m) for m in batch]

        # Encode
        t_enc = time.perf_counter()
        embeddings = model.encode(
            prompts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        enc_time = time.perf_counter() - t_enc

        # Update w bazie
        for movie, emb in zip(batch, embeddings):
            try:
                movie.embedding = emb.tolist()
                session.add(movie)
                updated += 1
            except Exception as e:
                errors += 1
                print(f"  ❌ {movie.title}: {e}")

        session.commit()

        elapsed = time.perf_counter() - t_start
        rate = updated / elapsed if elapsed > 0 else 0
        eta = (total - updated) / rate if rate > 0 else 0
        print(
            f"  [{batch_num:3d}/{total_batches}] "
            f"{updated:5d}/{total} filmów  "
            f"encode: {enc_time:.2f}s  "
            f"tempo: {rate:.0f} film/s  "
            f"ETA: {eta:.0f}s"
        )

    total_time = time.perf_counter() - t_start
    print(f"\n✅ Re-embedding zakończony!")
    print(f"   Zaktualizowano: {updated}/{total}")
    print(f"   Błędy: {errors}")
    print(f"   Czas: {total_time:.1f}s")

# ── Krok 4: Odbuduj HNSW index ──────────────────────────────────────

print(f"\n⏳ Tworzę HNSW index...")
t_idx = time.perf_counter()

with Session(engine) as session:
    session.exec(text(  # type: ignore
        "CREATE INDEX IF NOT EXISTS hnsw_movie "
        "ON movie USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200);"
    ))
    session.commit()

print(f"✅ HNSW index utworzony ({time.perf_counter() - t_idx:.1f}s)")

# ── Krok 5: Weryfikacja ─────────────────────────────────────────────

print(f"\n{'─'*60}")
print(f"  WERYFIKACJA")
print(f"{'─'*60}")

with Session(engine) as session:
    # Sprawdź wymiar
    result = session.exec(text(  # type: ignore
        "SELECT array_length(embedding::real[], 1) AS dim "
        "FROM movie WHERE embedding IS NOT NULL LIMIT 1;"
    )).first()

    if result:
        dim = result[0]
        status = "✅" if dim == NEW_DIM else "❌"
        print(f"  {status} Wymiar embeddingów: {dim} (oczekiwany: {NEW_DIM})")

    # Sprawdź ile ma embeddingi
    count = session.exec(text(  # type: ignore
        "SELECT COUNT(*) FROM movie WHERE embedding IS NOT NULL;"
    )).first()
    null_count = session.exec(text(  # type: ignore
        "SELECT COUNT(*) FROM movie WHERE embedding IS NULL;"
    )).first()
    print(f"  📊 Z embeddingiem: {count[0] if count else '?'}")
    print(f"  📊 Bez embeddingu: {null_count[0] if null_count else '?'}")

    # Sprawdź HNSW index
    idx = session.exec(text(  # type: ignore
        "SELECT indexname FROM pg_indexes WHERE indexname = 'hnsw_movie';"
    )).first()
    print(f"  {'✅' if idx else '❌'} HNSW index: {'istnieje' if idx else 'BRAK!'}")

print(f"\n{'='*60}")
print(f"  GOTOWE! Możesz teraz przebudować Docker.")
print(f"{'='*60}\n")

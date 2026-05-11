"""
Runner: uruchamia wszystkie 20 scenariuszy z test_datasets
przeciwko żywemu backendowi (Docker) i zapisuje wyniki do pliku .txt.

Użycie:
    python scripts/run_all_scenarios.py

Wymagania:
    - Backend musi być uruchomiony (docker compose up)
    - Ollama musi być dostępna
    - pip install requests  (powinno już być)

Wyniki trafiają do: scripts/results_<timestamp>.txt
"""

import sys
import os
import time
import json
import requests
from datetime import datetime
from uuid import uuid4

# ── Dodaj root projektu do sys.path ──────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from test.test_datasets import SCENARIOS

# ── Konfiguracja ─────────────────────────────────────────────────────

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8010")
TEST_EMAIL = f"scenario_runner_{uuid4().hex[:8]}@test.pl"
TEST_PASSWORD = "TestPassword123!"

# ── Plik wynikowy ────────────────────────────────────────────────────

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_FILE = os.path.join(PROJECT_ROOT, "scripts", f"results_{timestamp}.txt")


def log(msg: str, file=None):
    """Drukuje na konsole i zapisuje do pliku."""
    print(msg)
    if file:
        file.write(msg + "\n")
        file.flush()


def register_and_login(f) -> str:
    """Rejestruje test usera i loguje się — zwraca access_token."""
    log(f"\n{'='*70}", f)
    log(f"  REJESTRACJA I LOGOWANIE", f)
    log(f"{'='*70}", f)
    log(f"  Email: {TEST_EMAIL}", f)

    # Register
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
    }, timeout=30)

    if resp.status_code == 200:
        log(f"  ✅ Rejestracja OK: {resp.json()}", f)
    else:
        log(f"  ⚠️  Rejestracja: {resp.status_code} — {resp.text}", f)
        log(f"  (Kontynuuję — user może już istnieć)", f)

    # Login
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }, timeout=30)

    if resp.status_code != 200:
        log(f"  ❌ Login FAIL: {resp.status_code} — {resp.text}", f)
        sys.exit(1)

    data = resp.json()
    token = data["access_token"]
    log(f"  ✅ Login OK — user_id: {data.get('user_id')}", f)
    log(f"{'='*70}\n", f)
    return token


def build_movie_session_payload(scenario: dict) -> dict:
    """Konwertuje scenariusz z test_datasets do payloadu MovieSession."""
    host_user = scenario["users"][0]

    users_payload = []
    for u in scenario["users"]:
        users_payload.append({
            "user_id": u["user_id"],
            "user_name": u["user_name"],
            "personal_vibe": u["personal_vibe"],
        })

    return {
        "host_id": host_user["user_id"],
        "session_id": str(uuid4()),
        "invite_code": f"TEST{uuid4().hex[:4].upper()}",
        "meeting_type": scenario["meeting_type"],
        "is_active": True,
        "users": users_payload,
        "final_preferences": None,
    }


def run_scenario(idx: int, scenario: dict, token: str, f) -> dict:
    """Uruchamia jeden scenariusz: save session → get recommendation."""
    headers = {"Authorization": f"Bearer {token}"}
    result = {
        "name": scenario["name"],
        "meeting_type": scenario["meeting_type"],
        "users": [u["user_name"] for u in scenario["users"]],
        "success": False,
        "error": None,
        "session_id": None,
        "recommendation": None,
        "time_save": None,
        "time_recommend": None,
    }

    log(f"\n{'─'*70}", f)
    log(f"  [{idx:2d}/20] {scenario['name']}", f)
    log(f"  Typ: {scenario['meeting_type']}  |  Userzy: {', '.join(result['users'])}", f)
    log(f"  Opis: {scenario['description']}", f)
    log(f"{'─'*70}", f)

    # ── Krok 1: Zapisz sesję do bazy ─────────────────────────────────
    payload = build_movie_session_payload(scenario)

    log(f"  → POST /recommendation/session ...", f)
    t0 = time.perf_counter()
    try:
        resp = requests.post(
            f"{BASE_URL}/recommendation/session",
            json=payload,
            headers=headers,
            timeout=60,
        )
    except requests.exceptions.RequestException as e:
        result["error"] = f"Połączenie nie powiodło się: {e}"
        log(f"  ❌ {result['error']}", f)
        return result

    t1 = time.perf_counter()
    result["time_save"] = round(t1 - t0, 2)

    if resp.status_code != 200:
        result["error"] = f"Save session failed: {resp.status_code} — {resp.text[:500]}"
        log(f"  ❌ {result['error']}", f)
        return result

    session_id = resp.json().get("session_id")
    result["session_id"] = session_id
    log(f"  ✅ Sesja zapisana: {session_id}  ({result['time_save']}s)", f)

    # ── Krok 2: Pobierz rekomendacje (ciężkie AI) ───────────────────
    log(f"  → POST /recommendation/{session_id} ...", f)
    t2 = time.perf_counter()
    try:
        resp = requests.post(
            f"{BASE_URL}/recommendation/{session_id}",
            headers=headers,
            timeout=300,  # LLM może być wolny
        )
    except requests.exceptions.RequestException as e:
        result["error"] = f"Połączenie AI nie powiodło się: {e}"
        log(f"  ❌ {result['error']}", f)
        return result

    t3 = time.perf_counter()
    result["time_recommend"] = round(t3 - t2, 2)

    if resp.status_code != 200:
        result["error"] = f"Recommendation failed: {resp.status_code} — {resp.text[:500]}"
        log(f"  ❌ {result['error']}", f)
        return result

    recommendation = resp.json()
    result["recommendation"] = recommendation
    result["success"] = True

    # ── Pretty-print wyniku ──────────────────────────────────────────
    log(f"  ✅ Rekomendacja OK  ({result['time_recommend']}s)", f)
    log(f"", f)
    log(f"  🎬 GŁÓWNY FILM: {recommendation.get('movie_title', '???')}", f)
    log(f"     Gatunki:     {', '.join(recommendation.get('genres', []))}", f)
    log(f"     Ocena:       {recommendation.get('rating', 'N/A')}", f)
    log(f"     Runtime:     {recommendation.get('runtime', 'N/A')} min", f)
    log(f"     Data:        {recommendation.get('release_date', 'N/A')}", f)
    log(f"     Poster:      {recommendation.get('poster_path', 'N/A')}", f)
    log(f"", f)
    log(f"  💭 THOUGHT:", f)
    thought = recommendation.get("thought", "")
    for line in thought.split("\n"):
        log(f"     {line}", f)
    log(f"", f)
    log(f"  📝 REASONING:", f)
    reasoning = recommendation.get("reasoning_pl", "")
    for line in reasoning.split("\n"):
        log(f"     {line}", f)

    extras = recommendation.get("extra_movies", [])
    if extras:
        log(f"", f)
        log(f"  🎥 ALTERNATYWY:", f)
        for i, ex in enumerate(extras, 1):
            log(f"     {i}. {ex.get('movie_title', '???')}  "
                f"({', '.join(ex.get('genres', []))})  "
                f"⭐{ex.get('rating', 'N/A')}  "
                f"🕐{ex.get('runtime', 'N/A')}min", f)

    return result


def print_summary(results: list, total_time: float, f):
    """Drukuje podsumowanie po wszystkich scenariuszach."""
    log(f"\n\n{'═'*70}", f)
    log(f"  PODSUMOWANIE", f)
    log(f"{'═'*70}", f)

    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    log(f"  ✅ Udane:    {passed}/20", f)
    log(f"  ❌ Błędy:    {failed}/20", f)
    log(f"  ⏱️  Czas:     {total_time:.1f}s  (średnio {total_time/len(results):.1f}s/scenariusz)", f)

    if failed:
        log(f"\n  BŁĘDY:", f)
        for r in results:
            if not r["success"]:
                log(f"    ✗ {r['name']}: {r['error']}", f)

    # Tabela wyników
    log(f"\n  {'Nr':<4} {'Scenariusz':<35} {'Film':<30} {'Czas':<8} {'Status'}", f)
    log(f"  {'─'*4} {'─'*35} {'─'*30} {'─'*8} {'─'*6}", f)
    for i, r in enumerate(results, 1):
        movie = "—"
        if r["recommendation"]:
            movie = r["recommendation"].get("movie_title", "???")[:29]
        t = f"{(r['time_recommend'] or 0):.1f}s"
        status = "✅" if r["success"] else "❌"
        log(f"  {i:<4} {r['name']:<35} {movie:<30} {t:<8} {status}", f)

    log(f"\n{'═'*70}", f)
    log(f"  Wyniki zapisane do: {RESULTS_FILE}", f)
    log(f"{'═'*70}\n", f)


def main():
    print(f"\n🎬 movieNight Scenario Runner")
    print(f"   Backend: {BASE_URL}")
    print(f"   Scenariuszy: {len(SCENARIOS)}")
    print(f"   Plik wynikowy: {RESULTS_FILE}\n")

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        # Nagłówek
        log(f"{'═'*70}", f)
        log(f"  movieNight — Wyniki scenariuszy testowych", f)
        log(f"  Data:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f)
        log(f"  Backend: {BASE_URL}", f)
        log(f"  Scenariuszy: {len(SCENARIOS)}", f)
        log(f"{'═'*70}", f)

        # Auth
        token = register_and_login(f)

        # Uruchom scenariusze
        results = []
        total_start = time.perf_counter()

        for idx, scenario in enumerate(SCENARIOS, 1):
            result = run_scenario(idx, scenario, token, f)
            results.append(result)

            # Krótka pauza żeby nie trafić w rate limit (2/min na ciężkim endpoincie)
            if idx < len(SCENARIOS):
                wait_time = 32  # bezpieczny margines przy limicie 2/min
                log(f"\n  ⏳ Czekam {wait_time}s przed kolejnym scenariuszem (rate limit)...", f)
                time.sleep(wait_time)

        total_time = time.perf_counter() - total_start

        # Podsumowanie
        print_summary(results, total_time, f)

        # Zapisz surowy JSON z wynikami
        json_file = RESULTS_FILE.replace(".txt", ".json")
        with open(json_file, "w", encoding="utf-8") as jf:
            json.dump(results, jf, ensure_ascii=False, indent=2, default=str)
        log(f"  Surowe dane JSON: {json_file}", f)


if __name__ == "__main__":
    main()

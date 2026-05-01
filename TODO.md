# movieNight — TODO

## 🔴 Krytyczne (przed beta deployem)

- [ ] **CORS** — zmienić `allow_origins=["*"]` na `origins` listę z `groupmovie.com` (main.py L51)
- [ ] **Rate limiter na `/preferences`** — ✅ dodano `@limiter.limit()` na oba endpointy (10/min zapis, 30/min odczyt)
- [ ] **`/preferences/get`** — ✅ dodano weryfikację właściciela (403 dla innego user_id)
- [ ] **Refresh token** — ✅ zaimplementowano: `POST /auth/refresh` z token rotation, access 25min / refresh 7dni
- [ ] **Testy** — przynajmniej smoke testy na auth + recommendation flow

---

## 🟡 Ważne (stabilność i UX)

- [ ] **Lobby (REST API)** — endpoint do tworzenia pokoju przed sesją rekomendacji
- [ ] **poster_path + rok** — uzupełnić dane filmów w bazie (TMDB)
- [ ] **`user_taste` vector** — pole istnieje w modelu `User` ale nigdzie nie jest wypełniane ("coming soon")
- [ ] **`is_active` na sesji** — flaga `Room_Session.is_active` nie jest nigdzie zmieniana/sprawdzana
- [ ] **Obsługa błędów w `_add_db()`** — brak `try/except`, błąd DB nie jest obsłużony
- [ ] **`created_at` jako datetime** — teraz to `date`, lepiej zmienić na `datetime` z timezone

---

## 🟢 Przyszłość (po beta)

- [ ] **Rating endpoint** — model `Rating` istnieje w DB ale brak routera
- [ ] **GhostUser** — użytkownik bez konta w sesji
- [ ] **Metryki rekomendacji** — jak dobrze poleca (precision, kliknięcia, rating po seansie)
- [ ] **LLM as judge** — automatyczna ocena jakości rekomendacji
- [ ] **`user_taste` learning** — aktualizacja wektora użytkownika po każdym ratingu
- [ ] **Deploy (production)** — po zebraniu feedbacku z beta

---

## ✅ Zrobione

- [x] JWT auth (login + register)
- [x] Rate limiting (auth + recommendation + preferences)
- [x] Refresh token (`POST /auth/refresh`, token rotation, access 25min / refresh 7dni)
- [x] Podział recommendation endpointu na `/session` i `/{session_id}`
- [x] Hybrid search (vector + reranker)
- [x] Docker + compose.yaml
- [x] README + LICENSE
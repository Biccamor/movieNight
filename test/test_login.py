"""
Testy jednostkowe endpointów logowania i tokenów.

Pokrycie:
- Login sukces / złe hasło / nieistniejący user
- Struktura odpowiedzi
- Walidacja JWT tokena
- Refresh token flow
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from scripts.security import signJWT, hash_password


# ─── Helpers ────────────────────────────────────────────────────────

def _make_mock_user(email: str = "user@test.pl", password: str = "TestPassword123!"):
    """Tworzy mock obiektu User z bazy z zahashowanym hasłem."""
    user = MagicMock()
    user.user_id = uuid4()
    user.email = email
    user.hash_password = hash_password(password)
    return user


# ─── Login success ──────────────────────────────────────────────────

@patch("routers.auth_router.verify_password")
@patch("routers.auth_router.select")
def test_login_success(mock_select, mock_verify, client, mock_db):
    """Poprawny email + hasło → 200, zwraca tokeny i user_id."""
    mock_user = _make_mock_user()
    mock_verify.return_value = True

    # session.exec(statement).first() → mock_user
    mock_db.exec.return_value.first.return_value = mock_user

    response = client.post("/auth/login", json={
        "email": "user@test.pl",
        "password": "TestPassword123!",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"User user@test.pl logged in"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# ─── Login wrong password ──────────────────────────────────────────

@patch("routers.auth_router.verify_password")
@patch("routers.auth_router.select")
def test_login_wrong_password(mock_select, mock_verify, client, mock_db):
    """Poprawny email, złe hasło → 401."""
    mock_user = _make_mock_user()
    mock_verify.return_value = False

    mock_db.exec.return_value.first.return_value = mock_user

    response = client.post("/auth/login", json={
        "email": "user@test.pl",
        "password": "WrongPassword999!",
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong e-mail or password"


# ─── Login nonexistent user ────────────────────────────────────────

@patch("routers.auth_router.select")
def test_login_nonexistent_user(mock_select, client, mock_db):
    """Nieistniejący email → 401."""
    mock_db.exec.return_value.first.return_value = None

    response = client.post("/auth/login", json={
        "email": "ghost@test.pl",
        "password": "Whatever123!",
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong e-mail or password"


# ─── Response structure ────────────────────────────────────────────

@patch("routers.auth_router.verify_password")
@patch("routers.auth_router.select")
def test_login_response_structure(mock_select, mock_verify, client, mock_db):
    """Odpowiedź zawiera wymagane klucze."""
    mock_user = _make_mock_user()
    mock_verify.return_value = True
    mock_db.exec.return_value.first.return_value = mock_user

    response = client.post("/auth/login", json={
        "email": "user@test.pl",
        "password": "TestPassword123!",
    })

    data = response.json()
    expected_keys = {"message", "access_token", "refresh_token", "token_type", "user_id"}
    assert expected_keys == set(data.keys())


# ─── Token is valid JWT ────────────────────────────────────────────

@patch("routers.auth_router.verify_password")
@patch("routers.auth_router.select")
def test_login_token_is_valid_jwt(mock_select, mock_verify, client, mock_db):
    """Zwrócony access_token jest poprawnym JWT z user_id i type=access."""
    import jwt
    from schemas.schemas import Settings

    setting = Settings()  # type: ignore
    mock_user = _make_mock_user()
    mock_verify.return_value = True
    mock_db.exec.return_value.first.return_value = mock_user

    response = client.post("/auth/login", json={
        "email": "user@test.pl",
        "password": "TestPassword123!",
    })

    token = response.json()["access_token"]
    payload = jwt.decode(token, setting.secret_key, algorithms=[setting.algorithm])

    assert payload["type"] == "access"
    assert payload["user_id"] == str(mock_user.user_id)


# ─── Refresh token success ─────────────────────────────────────────

def test_refresh_token_success(client, mock_db):
    """Poprawny refresh token → nowa para tokenów."""
    user_id = str(uuid4())
    tokens = signJWT(user_id)

    response = client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"],
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # Nowe tokeny powinny być inne niż stare
    assert data["access_token"] != tokens["access_token"]


# ─── Refresh with access token fails ───────────────────────────────

def test_refresh_with_access_token_fails(client, mock_db):
    """Próba użycia access_token jako refresh → 401."""
    user_id = str(uuid4())
    tokens = signJWT(user_id)

    response = client.post("/auth/refresh", json={
        "refresh_token": tokens["access_token"],  # celowo access zamiast refresh
    })

    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]

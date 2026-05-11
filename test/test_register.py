"""
Testy jednostkowe rejestracji użytkownika.

Pokrycie:
- Rejestracja sukces
- Rejestracja — email już istnieje
"""

import pytest
from unittest.mock import patch


# ─── Rejestracja sukces ─────────────────────────────────────────────

@patch("routers.auth_router.check_if_email_exists")
def test_create_account_success(mock_check_email, client, mock_db):
    """Nowy email + poprawne hasła → 200, konto utworzone."""
    mock_check_email.return_value = False

    payload = {
        "email": "nowy@test.pl",
        "password": "SuperSecretPassword123!",
        "confirm_password": "SuperSecretPassword123!"
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Account created successfully"
    assert "user_id" in response.json()

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


# ─── Rejestracja — email już istnieje ──────────────────────────────

@patch("routers.auth_router.check_if_email_exists")
def test_create_account_email_exists(mock_check_email, client, mock_db):
    """Istniejący email → 400."""
    mock_check_email.return_value = True

    payload = {
        "email": "istniejacy@test.pl",
        "password": "SomePassword!",
        "confirm_password": "SomePassword!"
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Account with this email adress already exists"

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
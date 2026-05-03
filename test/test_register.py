import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from database.main_db import get_session
client = TestClient(app)

# Mock database
@pytest.fixture
def mock_db_session():

    session = MagicMock()
    
    app.dependency_overrides[get_session] = lambda: session
    
    yield session

    app.dependency_overrides.clear()


# 2. Test ścieżki sukcesu (rejestracja przechodzi)
@patch("routers.auth_router.check_if_email_exists") 
def test_create_account_success(mock_check_email, mock_db_session):
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
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()


# 3. Test błędu (użytkownik już istnieje)
@patch("routers.auth_router.check_if_email_exists")
def test_create_account_email_exists(mock_check_email, mock_db_session):
    mock_check_email.return_value = True
    
    payload = {
        "email": "istniejacy@test.pl",
        "password": "SomePassword!",
        "confirm_password": "SomePassword!"
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Account with this email adress already exists"
    
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()
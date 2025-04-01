import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.link import Link
from app.core.security import hash_password

test_user_data = {"username": "testuser", "email": "test@example.com", "password": "testpass"}
test_user2_data = {"username": "testuser2", "email": "test2@example.com", "password": "testpass2"}

def create_test_user(db: Session, user_data: dict = test_user_data):
    user = User(
        username=user_data["username"],
        email=user_data["email"],
        password_hash=hash_password(user_data["password"])
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_link(db: Session, user_id: int, short_code: str = "test123"):
    link = Link(
        original_url="https://example.com",
        short_code=short_code,
        created_by_id=user_id
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

@pytest.fixture
def client(db):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers(client, db):
    create_test_user(db)
    login_resp = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": test_user_data["password"]})
    return {"Cookie": f"session_id={login_resp.cookies['session_id']}"}

@pytest.fixture
def auth_headers2(client, db):
    create_test_user(db, test_user2_data)
    login_resp = client.post("/api/auth/login", json={"username": test_user2_data["username"], "password": test_user2_data["password"]})
    return {"Cookie": f"session_id={login_resp.cookies['session_id']}"}

def test_register(client, db):
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == test_user_data["username"]
    
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Имя пользователя уже используется" in response.json()["detail"]

def test_register_with_existing_email(client, db):
    create_test_user(db)
    new_user_data = {
        "username": "newuser",
        "email": test_user_data["email"],
        "password": "newpass"
    }
    response = client.post("/api/auth/register", json=new_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email уже используется" in response.json()["detail"]

def test_login(client, db):
    create_test_user(db)
    
    response = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": test_user_data["password"]})
    assert response.status_code == status.HTTP_200_OK
    assert "session_id" in response.cookies
    
    response = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": "wrongpass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Неверные учетные данные" in response.json()["detail"]

def test_login_sets_proper_cookie(client, db):
    create_test_user(db)
    
    response = client.post("/api/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    
    # Проверяем параметры cookie
    cookie = response.cookies.get("session_id")
    assert cookie is not None
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Path=/" in response.headers["set-cookie"]
    assert "Max-Age=86400" in response.headers["set-cookie"]

def test_login_with_nonexistent_user(client):
    response = client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": "anypassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Неверные учетные данные" in response.json()["detail"]

def test_logout(client, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get("session_id") == None

def test_logout_without_session(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get("session_id") is None

def test_profile_unauthorized(client):
    response = client.get("/api/auth/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_user_unauthorized(client):
    response = client.delete("/api/auth/user")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_profile(client, auth_headers):
    response = client.get("/api/auth/profile", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user_data["username"]

def test_delete_user(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id)
    
    response = client.delete("/api/auth/user", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Пользователь удалён"
    
    assert db.query(User).filter(User.username == test_user_data["username"]).first() is None
    assert db.query(Link).filter(Link.created_by_id == user.id).first() is None

def test_get_current_user_invalid_token(client):
    # Пытаемся получить профиль с неверным токеном
    response = client.get("/api/auth/profile", headers={"Cookie": "session_id=invalid"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user_expired_token(client, db, monkeypatch):
    # Создаем пользователя
    user = create_test_user(db)
    
    # Мокаем create_session чтобы вернуть "просроченный" токен
    def mock_create_session(*args, **kwargs):
        return "expired_token"
    
    monkeypatch.setattr("app.core.security.create_session", mock_create_session)
    
    # Логинимся чтобы получить "просроченный" токен
    login_resp = client.post("/api/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    
    # Пытаемся получить профиль с "просроченным" токеном
    response = client.get("/api/auth/profile", 
                        headers={"Cookie": f"session_id={login_resp.cookies['session_id']}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_user_out_schema(client, db, auth_headers):
    response = client.get("/api/auth/profile", headers=auth_headers)
    assert "username" in response.json()
    assert "email" in response.json()
    assert "password" not in response.json()  # проверяем что пароль не возвращается

def test_create_link(client, auth_headers):
    response = client.post("/api/links/", json={"original_url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert "short_code" in response.json()
    
    custom_alias = "custom123"
    response = client.post("/api/links/", json={"original_url": "https://example.com", "custom_alias": custom_alias}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["short_code"] == custom_alias
    
    response = client.post("/api/links/", json={"original_url": "https://example.com", "custom_alias": custom_alias}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Такой alias уже используется" in response.json()["detail"]

def test_list_links(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test1")
    create_test_link(db, user.id, "test2")
    
    response = client.get("/api/links/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2

def test_search_link(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.get("/api/links/search", params={"original_url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["short_code"] == "test123"
    
    response = client.get("/api/links/search", params={"original_url": "https://nonexistent.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_link(client, db, auth_headers, auth_headers2):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.get("/api/links/test123", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["short_code"] == "test123"
    
    response = client.get("/api/links/test123", headers=auth_headers2)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    response = client.get("/api/links/nonexistent", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_link(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    update_data = {"original_url": "https://updated.com"}
    response = client.put("/api/links/test123", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["original_url"] == "https://updated.com"
    
    update_data = {"expires_in_days": 7}
    response = client.put("/api/links/test123", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["expires_at"] is not None

def test_delete_link(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.delete("/api/links/test123", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert db.query(Link).filter(Link.short_code == "test123").first() is None

def test_get_link_stats(client, db, auth_headers):
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.get("/api/links/test123/stats", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["original_url"] == "https://example.com"
    assert "access_count" in response.json()
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
    user = create_test_user(db)
    login_resp = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": test_user_data["password"]})
    return {"Cookie": f"session_id={login_resp.cookies['session_id']}"}

@pytest.fixture
def auth_headers2(client, db):
    user = create_test_user(db, test_user2_data)
    login_resp = client.post("/api/auth/login", json={"username": test_user2_data["username"], "password": test_user2_data["password"]})
    return {"Cookie": f"session_id={login_resp.cookies['session_id']}"}

# Auth tests
def test_register(client, db):
    # Test successful registration
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == test_user_data["username"]
    
    # Test duplicate username
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Имя пользователя уже используется" in response.json()["detail"]

def test_login(client, db):
    create_test_user(db)
    
    # Test successful login
    response = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": test_user_data["password"]})
    assert response.status_code == status.HTTP_200_OK
    assert "session_id" in response.cookies
    
    # Test invalid credentials
    response = client.post("/api/auth/login", json={"username": test_user_data["username"], "password": "wrongpass"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Неверные учетные данные" in response.json()["detail"]

def test_logout(client, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get("session_id") == None

def test_profile(client, auth_headers):
    response = client.get("/api/auth/profile", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user_data["username"]

def test_delete_user(client, db, auth_headers):
    # First create a link for the user
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id)
    
    response = client.delete("/api/auth/user", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Пользователь удалён"
    
    # Verify user and links are deleted
    assert db.query(User).filter(User.username == test_user_data["username"]).first() is None
    assert db.query(Link).filter(Link.created_by_id == user.id).first() is None

# Link tests
def test_create_link(client, auth_headers):
    # Test simple link creation
    response = client.post("/api/links/", json={"original_url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert "short_code" in response.json()
    
    # Test with custom alias
    custom_alias = "custom123"
    response = client.post("/api/links/", json={"original_url": "https://example.com", "custom_alias": custom_alias}, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["short_code"] == custom_alias
    
    # Test duplicate custom alias
    response = client.post("/api/links/", json={"original_url": "https://example.com", "custom_alias": custom_alias}, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Такой alias уже используется" in response.json()["detail"]

def test_list_links(client, db, auth_headers):
    # First create some links
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test1")
    create_test_link(db, user.id, "test2")
    
    response = client.get("/api/links/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2

def test_search_link(client, db, auth_headers):
    # First create a link
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.get("/api/links/search", params={"original_url": "https://example.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["short_code"] == "test123"
    
    # Test non-existent link
    response = client.get("/api/links/search", params={"original_url": "https://nonexistent.com"}, headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_link(client, db, auth_headers, auth_headers2):
    # First create a link
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    # Test owner can access
    response = client.get("/api/links/test123", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["short_code"] == "test123"
    
    # Test other user can't access
    response = client.get("/api/links/test123", headers=auth_headers2)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Test non-existent link
    response = client.get("/api/links/nonexistent", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_link(client, db, auth_headers):
    # First create a link
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    # Test update URL
    update_data = {"original_url": "https://updated.com"}
    response = client.put("/api/links/test123", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["original_url"] == "https://updated.com"
    
    # Test update expiration
    update_data = {"expires_in_days": 7}
    response = client.put("/api/links/test123", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["expires_at"] is not None

def test_delete_link(client, db, auth_headers):
    # First create a link
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.delete("/api/links/test123", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify link is deleted
    assert db.query(Link).filter(Link.short_code == "test123").first() is None

def test_get_link_stats(client, db, auth_headers):
    # First create a link
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    create_test_link(db, user.id, "test123")
    
    response = client.get("/api/links/test123/stats", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["original_url"] == "https://example.com"
    assert "access_count" in response.json()
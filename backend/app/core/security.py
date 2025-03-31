import uuid
from passlib.context import CryptContext
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.database import get_db
from app.core.config import SESSION_TTL
from app.core.cache import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_session(user_id: int) -> str:
    session_token = str(uuid.uuid4())
    redis_client.setex(f"session:{session_token}", SESSION_TTL, user_id)
    return session_token

def delete_session(session_token: str):
    redis_client.delete(f"session:{session_token}")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(status_code=401, detail="Не авторизован")
    user_id = redis_client.get(f"session:{session_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Сессия недействительна или истекла")
    try:
        user_id = int(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Некорректная сессия")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user
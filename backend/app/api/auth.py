from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session

from app.models.link import Link
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.models.user import User
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_session,
    delete_session,
    get_current_user
)

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Имя пользователя уже используется")
    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(user_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    session_token = create_session(user.id)
    response.set_cookie(key="session_id", value=session_token, httponly=True, max_age=86400, path="/")
    return {"message": "Успешный вход", "user": {"id": user.id, "username": user.username}}

@router.post("/logout")
def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_id")
    if session_token:
        delete_session(session_token)
    response.delete_cookie("session_id", path="/")
    return {"message": "Вы вышли из системы"}

@router.get("/profile", response_model=UserOut)
def profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.delete("/user", response_model=dict)
def delete_user(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Link).filter(Link.created_by_id == current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"message": "Пользователь удалён"}
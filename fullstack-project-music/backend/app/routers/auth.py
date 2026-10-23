from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import users as users_repo
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password



router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserOut)
def register_user(body: UserCreate, db: Session = Depends(get_db)):
    if users_repo.get_by_email(db=db, email=body.email) is not None:
        raise HTTPException(status_code=409, detail=f"Email {body.email} already registered")
    return users_repo.create_user(db=db, email=body.email, password_hash=hash_password(body.password))


@router.post("/login", response_model=Token)
def login_user(body: UserCreate, db: Session = Depends(get_db)):
    user = users_repo.get_by_email(db=db, email=body.email)
    if user is None or not verify_password(password=body.password, password_hash=user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.id))


@router.delete("/logout", response_model=None, status_code=204)
def logout_user():
    raise HTTPException(status_code=501, detail="Not implemented")



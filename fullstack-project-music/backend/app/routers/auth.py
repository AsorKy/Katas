from fastapi import APIRouter, HTTPException

from app.schemas import UserCreate, UserOut, Token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserOut)
def register_user(body: UserCreate):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/login", response_model=Token)
def login_user(body: UserCreate):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/logout", response_model=None, status_code=204)
def logout_user():
    raise HTTPException(status_code=501, detail="Not implemented")



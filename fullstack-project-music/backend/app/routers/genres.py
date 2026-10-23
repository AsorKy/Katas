from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import genres as genres_repo
from app.schemas import GenreOut

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)):
    return genres_repo.list_genres(db)




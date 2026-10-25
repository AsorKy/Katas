from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import stats as stats_repo
from app.schemas import GenreStats
from app.services import stats as stats_service


router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/top-genres", response_model=list[GenreStats])
def top_genres(limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    rows = stats_repo.genre_rows(db)
    return stats_service.top_genres(rows, limit)
from fastapi import APIRouter , HTTPException

from app.schemas import GenreOut

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres():
    raise HTTPException(status_code=501, detail="Not implemented")




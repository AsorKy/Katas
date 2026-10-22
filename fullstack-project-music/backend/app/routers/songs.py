from fastapi import APIRouter, HTTPException, Query

from app.schemas import SongCreate, SongsOut


router = APIRouter(prefix="/songs", tags=["songs"])


@router.post("", status_code=201,response_model=SongsOut)
def create_song(body: SongCreate):
    raise HTTPException(status_code=501, detail="Not implemented")
    

@router.get("", response_model=list[SongsOut])
def list_songs(
    genre_id: int | None = None,
    artist_id: int | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{song_id}", response_model=SongsOut)
def get_song(song_id: int):
    raise HTTPException(status_code=501, detail="Not implemented")


# @router.delete("/{song_id}", response_model=None ,status_code=204)
# def delete_song(song_id: int):
#     raise HTTPException(status_code=501, detail="Not implemented")



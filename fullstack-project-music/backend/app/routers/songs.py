from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db 
from app.repositories import songs as songs_repo
from app.schemas import SongCreate, SongsOut


router = APIRouter(prefix="/songs", tags=["songs"])


@router.post("", status_code=201,response_model=SongsOut)
def create_song(body: SongCreate):
    raise HTTPException(status_code=501, detail="Not implemented")
    

@router.get("", response_model=list[SongsOut])
def list_songs(
    db: Session = Depends(get_db),
    genre_id: int | None = None,
    artist_id: int | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
    if songs is None or []:
        raise HTTPException(status_code=404, detail="No songs found")
    return songs


@router.get("/{song_id}", response_model=SongsOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = songs_repo.get_song(db, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")
    return song


    #raise HTTPException(status_code=501, detail="Not implemented")


# @router.delete("/{song_id}", response_model=None ,status_code=204)
# def delete_song(song_id: int):
#     raise HTTPException(status_code=501, detail="Not implemented")



from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import songs as songs_repo
from app.schemas import SongCreate, SongsOut, SimilarSong
from app.depends import current_user
from app.services import songs as songs_service
from app.services import similarity as similarity_service

router = APIRouter(prefix="/songs", tags=["songs"])


@router.post("", status_code=201, response_model=SongsOut, dependencies=[Depends(current_user)])
def create_song(body: SongCreate, db: Session = Depends(get_db)):
    try:
        return songs_service.create_song(db, body)
    except songs_service.RelatedNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    

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
    #if songs is None or []:
    #    raise HTTPException(status_code=200, detail="No songs found")
    return songs


@router.get("/{song_id}", response_model=SongsOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = songs_repo.get_song(db, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")
    return song


@router.get("/{song_id}/similar", response_model=list[SimilarSong])
def similar_song(song_id: int, limit:int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    if not songs_repo.get_song(db, song_id):
        raise HTTPException(status_code=404, detail=f"Song {song_id} not fount")
    return similarity_service.similar_songs(db, song_id, limit)







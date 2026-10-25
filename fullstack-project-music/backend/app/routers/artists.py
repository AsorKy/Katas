from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import artists as artists_repo
from app.repositories import songs as songs_repo
from app.schemas import ArtistsCreate, ArtistsOut, ArtistStats, SongsOut
from app.depends import current_user


router = APIRouter(prefix="/artists", tags=["artists"])


@router.post("", status_code=201, response_model=ArtistsOut, dependencies=[Depends(current_user)])
def create_artist(body: ArtistsCreate, db: Session = Depends(get_db)):
    if artists_repo.get_by_name(db=db, name=body.name) is not None:
        raise HTTPException(status_code=409, detail=f"Artist {body.name!r} already exists")
    return artists_repo.create_artist(db=db, name=body.name)



@router.get("", response_model=list[ArtistsOut])
def list_artists(
    db: Session = Depends(get_db),
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    artists = artists_repo.list_artists(db, q, limit, offset)
    return artists



@router.get("/{artist_id}", response_model=ArtistsOut)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = artists_repo.get_artist(db, artist_id)
    if artist is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found.")
    return artist


@router.get("/{artist_id}/songs", response_model=list[SongsOut])
def get_artist_songs(artist_id: int,db: Session = Depends(get_db)):
    if artists_repo.get_artist(db, artist_id) is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found.")
    songs = songs_repo.list_songs(db=db, artist_id=artist_id)
    return songs


@router.get("/{artist_id}/stats", response_model=ArtistStats)
def get_artist_stats(artist_id: int, db: Session = Depends(get_db)):
    artist_stats = artists_repo.get_stats(db, artist_id)
    if artist_stats is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} stats not found.")
    return artist_stats

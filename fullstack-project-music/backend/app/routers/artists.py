from fastapi import APIRouter, HTTPException, Query

from app.schemas import ArtistsCreate, ArtistsOut, ArtistStats, SongsOut


router = APIRouter(prefix="/artists", tags=["artists"])


@router.post("", status_code=201,response_model=ArtistsOut)
def create_artist(body: ArtistsCreate):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=list[ArtistsOut])
def list_artists(
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{artist_id}", response_model=ArtistsOut)
def get_artist(artist_id: int):
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/{artist_id}/songs", response_model=list[SongsOut])
def get_artist_songs(artist_id:int):
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/{artist_id}/stats", response_model=ArtistStats)
def get_artist_stats(artist_id: int):
    raise HTTPException(status_code=501, detail="Not Implemented")


# @router.delete("/{artist_id}", status_code=204)
# def delete_artist(artist_id: int):
#     raise HTTPException(status_code=501, detail="Not Implemented")

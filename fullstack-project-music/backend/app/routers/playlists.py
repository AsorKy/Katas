from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app import models
from app.schemas import PlaylistAddSong, PlaylistDetail, PlaylistOut, PlaylistsCreate
from app.depends import current_user, owned_playlist
from app.repositories import playlists as playlists_repo
from app.services import playlists as playlists_service


router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post("", status_code=201, response_model=PlaylistOut)
def create_playlist(body: PlaylistsCreate, user: models.User = Depends(current_user),
                    db: Session = Depends(get_db)):
    return playlists_repo.create_playlist(db=db, owner_id=user.id, name=body.name)


@router.get("", response_model=list[PlaylistOut])
def get_playlists(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    return playlists_repo.list_playlists(db=db, owner_id=user.id)


@router.get("/{playlist_id}", response_model=PlaylistDetail)
def get_playlist(
    playlist: models.Playlist = Depends(owned_playlist), 
    db: Session = Depends(get_db)
    ):
    return playlists_repo.get_detail(db=db, playlist=playlist)


@router.post("/{playlist_id}/songs", status_code=201, response_model=PlaylistDetail)
def add_song_to_playlist(
    body: PlaylistAddSong,
    playlist: models.Playlist = Depends(owned_playlist),
    db: Session = Depends(get_db),
):
    try:
        return playlists_service.add_song(db, playlist, body.song_id)
    except playlists_service.SongNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except playlists_service.AlreadyInPlaylist as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{playlist_id}/songs/{song_id}", status_code=204)
def remove_song_from_playlist(
    song_id: int,
    playlist: models.Playlist = Depends(owned_playlist), 
    db: Session = Depends(get_db)
):
    if not playlists_repo.remove_song(db=db, playlist_id=playlist.id, song_id=song_id):
        raise HTTPException(status_code=404, detail=f"Song {song_id} is not in playlist {playlist.id}")

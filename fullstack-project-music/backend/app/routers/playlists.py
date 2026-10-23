from fastapi import APIRouter, HTTPException

from app.schemas import PlaylistAddSong, PlaylistDetail, PlaylistOut, PlaylistsCreate

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post("", status_code=201, response_model=PlaylistOut)
def create_playlist(body: PlaylistsCreate):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=list[PlaylistOut])
def get_playlists():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{playlist_id}", response_model=PlaylistDetail)
def get_playlist(playlist_id: int):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{playlist_id}/songs",status_code=201, response_model=PlaylistDetail)
def add_song_to_playlist(playlist_id: int, body: PlaylistAddSong):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{playlist_id}/songs/{song_id}",status_code=204)
def remove_song_from_playlist(playlist_id:int, song_id:int):
    raise HTTPException(status_code=501, detail="Not implemented")
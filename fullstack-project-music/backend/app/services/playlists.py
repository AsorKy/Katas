from sqlalchemy.orm import Session

from app import models
from app.repositories import playlists as playlists_repo
from app.repositories import songs as songs_repo


class SongNotFound(Exception):
    """La canción no existe."""


class AlreadyInPlaylist(Exception):
    """La canción ya está en la playlist."""


def add_song(db: Session, playlist: models.Playlist, song_id: int) -> dict:
    if not songs_repo.song_exists(db, song_id):
        raise SongNotFound(f"Song {song_id} not found")
    if playlists_repo.song_in_playlist(db, playlist.id, song_id):
        raise AlreadyInPlaylist(f"Song {song_id} is already in playlist {playlist.id}")
    playlists_repo.add_song(db, playlist.id, song_id)
    return playlists_repo.get_detail(db, playlist)
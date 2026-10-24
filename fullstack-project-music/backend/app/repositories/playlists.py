from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models
from app.repositories import songs as songs_repo



def create_playlist(db: Session, owner_id: int, name: str) -> models.Playlist:
    playlist = models.Playlist(name=name, owner_id=owner_id)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist



def list_playlists(db: Session, owner_id: int) -> list[models.Playlist]:
    smtm = select(models.Playlist).where(models.Playlist.owner_id == owner_id).order_by(models.Playlist.id)
    return list(db.scalars(smtm))



def get_playlists(db: Session, playlist_id: int, owner_id: int) -> models.Playlist | None:
    stmt = select(models.Playlist).where(
        models.Playlist.id == playlist_id, models.Playlist.owner_id == owner_id
    )
    return db.scalar(stmt)



def get_detail(db: Session, playlist: models.Playlist) -> dict:
    stmt = (
        select(models.Song)
        .join(models.PlaylistSong, models.PlaylistSong.song_id == models.Song.id)
        .where(models.PlaylistSong.playlist_id == playlist.id)
        .order_by(models.PlaylistSong.position)
    )
    songs = list(db.scalars(stmt))
    return {
        "id": playlist.id,
        "name": playlist.name,
        "songs": songs_repo.to_out(db=db, songs=songs)
    }



def song_in_playlist(db: Session, playlist_id: int, song_id: int) -> bool:
    return db.get(models.PlaylistSong, (playlist_id, song_id)) is not None



def add_song(db: Session, playlist_id: int, song_id: int) -> None:
    last = db.scalar(
        select(func.max(models.PlaylistSong.position))
        .where(models.PlaylistSong.playlist_id == playlist_id)
    )
    db.add(models.PlaylistSong(
        playlist_id=playlist_id,
        song_id=song_id,
        position=(last or 0) + 1,
    ))
    db.commit()



def remove_song(db: Session, playlist_id: int, song_id: int) -> bool:
    link = db.get(models.PlaylistSong, (playlist_id, song_id))
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True
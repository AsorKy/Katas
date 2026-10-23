from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session 

from app import models


def get_artist(db: Session, artist_id: int) -> dict | None:
    artist = db.get(models.Artist, artist_id)
    if artist is None:
        return None
    
    genres = list(db.scalars(
        select(models.Genre.name).distinct()
        .join(models.Song, models.Song.genre_id == models.Genre.id)
        .join(models.SongArtist, models.SongArtist.song_id == models.Song.id) 
        .where(models.SongArtist.artist_id == artist_id)
        .order_by(models.Genre.name)
    ))
    return {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "created_at": artist.created_at
    }


def list_artists(db: Session, q: str | None, limit: int, offset: int) -> list[dict]:
    stmt = select(models.Artist)
    if q:
        stmt = stmt.where(models.Artist.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(models.Artist.name).limit(limit).offset(offset)
    return [get_artist(db, a.id) for a in db.scalars(stmt)]


def get_stats(db: Session, artist_id:int) -> dict | None:
    artist = db.get(models.Artist, artist_id)
    if artist is None:
        return None

    song_count = db.scalar(
        select(func.count())
        .select_from(models.SongArtist)
        .where(models.SongArtist.artist_id == artist_id)
    )

    playlist_count = db.scalar(
        select(func.count(distinct(models.PlaylistSong.playlist_id)))
        .select_from(models.PlaylistSong)
        .join(models.SongArtist, models.SongArtist.song_id == models.PlaylistSong.song_id)
        .where(models.SongArtist.artist_id == artist_id)
    )

    return {
        "artist_id": artist_id,
        "song_count": song_count,
        "playlist_count": playlist_count
    }
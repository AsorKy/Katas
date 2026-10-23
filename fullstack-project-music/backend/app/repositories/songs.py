from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def _to_out(db:Session, songs: list[models.Song]) -> list[dict]:
    if not songs:
        return []
    
    # consulta 2: generos de todas las canciones de la pagina
    genre_ids = [s.genre_id for s in songs]
    genres = {
        g.id: g for g in db.scalars(select(models.Genre).where(models.Genre.id.in_(genre_ids)))
    }

    # consulta 3: artistas de todas las canciones con su rol
    rows = db.execute(
        select(models.SongArtist.song_id, models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, models.Artist.id == models.SongArtist.artist_id)
        .where(models.SongArtist.song_id.in_([s.id for s in songs]))
        .order_by(models.SongArtist.song_id, models.SongArtist.artist_id)
    ).all()

    by_song = defaultdict(list)
    for r in rows:
        by_song[r.song_id].append(
            {
                "artist_id": r.artist_id,
                "name": r.name,
                "role": r.role
            }
        )

    return [
        {
            "id": s.id, "title":  s.title, "duration_s": s.duration_s,
            "created_at": s.created_at, "genre": genres[s.genre_id],
            "artists": by_song[s.id]
        }
        for s in songs
    ]



def list_songs(
    db: Session, genre_id=None, artist_id=None, q=None,
    limit=None, offset=None
) -> list[dict]:

    stmt = select(models.Song)
    if genre_id is not None:
        stmt = stmt.where(models.Song.genre_id == genre_id)
    if artist_id is not None:
        stmt = stmt.where(
            models.Song.id.in_(
                select(models.SongArtist.song_id)
                .where(models.SongArtist.artist_id == artist_id)
            )
        )
    if q:
        stmt = stmt.where(models.Song.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(models.Song.id).limit(limit).offset(offset)
    return _to_out(db, list(db.scalars(stmt)))



def get_song(db:Session, song_id: int) -> dict | None:
    song = db.get(models.Song, song_id)
    if song is None:
        return None
    
    genre = db.get(models.Genre, song.genre_id)
    rows = db.execute(
        select(models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, models.SongArtist.artist_id == models.Artist.id)
        .where(models.SongArtist.song_id == song_id)
        .order_by(models.SongArtist.artist_id)
    ).all()

    return {
        "id": song.id,
        "title": song.title,
        "duration_s": song.duration_s,
        "created_at": song.created_at,
        "genre": genre,
        "artists": [{"artist_id": r.artist_id, "name": r.name, "role": r.role} for r in rows]
    }

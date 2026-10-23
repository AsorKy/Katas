from sqlalchemy.orm import Session

from app.repositories import songs as songs_repo
from app.schemas import SongCreate


class RelatedNotFound(Exception):
    """El género o algún artista de la canción no existe."""



def create_song(db: Session, body: SongCreate) -> dict:
    if not songs_repo.genre_exists(db, body.genre_id):
        raise RelatedNotFound(f"Genre {body.genre_id} not found")

    ids = [a.artist_id for a in body.artists]
    missing = sorted(set(ids) - songs_repo.existing_artist_ids(db=db, ids=ids))
    if missing:
        raise RelatedNotFound(f"Artist(s) {missing} not found")

    song_id = songs_repo.create_song(
        db=db,
        title=body.title,
        duration_s=body.duration_s,
        genre_id = body.genre_id,
        artists=[(a.artist_id, a.role) for a in body.artists]
    )
    return songs_repo.get_song(db, song_id)
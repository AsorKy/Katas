import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def genre_rows(db: Session) -> pd.DataFrame:
    stmt = (
        select(
            models.Genre.id.label("genre_id"),
            models.Genre.name,
            models.Song.id.label("song_id"),
            models.Song.duration_s,
            models.PlaylistSong.playlist_id,
        )
        .select_from(models.Genre)
        .outerjoin(models.Song, models.Song.genre_id == models.Genre.id)
        .outerjoin(models.PlaylistSong, models.PlaylistSong.song_id == models.Song.id)
    )
    return pd.read_sql(stmt, db.connection())
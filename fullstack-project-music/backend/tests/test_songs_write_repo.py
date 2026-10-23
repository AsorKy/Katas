"""Lección 7, Paso B: funciones de escritura de repositories/songs.py (sin HTTP)."""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import models
from app.repositories import songs as songs_repo


@pytest.fixture
def base(db_factory):
    with db_factory() as db:
        db.add_all([
            models.Genre(id=1, name="Rock"),
            models.Artist(id=1, name="Ana"),
            models.Artist(id=2, name="Beto"),
        ])
        db.commit()


def test_genre_exists(db_factory, base):
    with db_factory() as db:
        assert songs_repo.genre_exists(db, 1) is True
        assert songs_repo.genre_exists(db, 99) is False


def test_existing_artist_ids_returns_only_the_ones_that_exist(db_factory, base):
    with db_factory() as db:
        assert songs_repo.existing_artist_ids(db, [1, 2, 99]) == {1, 2}
        assert songs_repo.existing_artist_ids(db, [99]) == set()


def test_create_song_returns_id_and_links_every_artist(db_factory, base):
    with db_factory() as db:
        song_id = songs_repo.create_song(db, "Uno", 180, 1, [(1, "main"), (2, "featured")])
        assert song_id == 1
        song = songs_repo.get_song(db, song_id)
    assert song["title"] == "Uno" and song["duration_s"] == 180
    assert song["artists"] == [
        {"artist_id": 1, "name": "Ana", "role": "main"},
        {"artist_id": 2, "name": "Beto", "role": "featured"},
    ]


def test_create_song_is_committed(db_factory, base):
    with db_factory() as s1:
        songs_repo.create_song(s1, "Uno", 180, 1, [(1, "main")])
    with db_factory() as s2:                       # otra sesión, como otra petición HTTP
        assert s2.scalar(select(models.Song.title)) == "Uno"


def test_failure_midway_leaves_no_orphan_song(db_factory, base):
    """El artista 99 no existe: falla al vincular. La canción NO debe quedar guardada."""
    with db_factory() as s1:
        with pytest.raises(IntegrityError):
            songs_repo.create_song(s1, "Uno", 180, 1, [(1, "main"), (99, "featured")])
    with db_factory() as s2:
        assert s2.scalars(select(models.Song)).all() == []
        assert s2.scalars(select(models.SongArtist)).all() == []

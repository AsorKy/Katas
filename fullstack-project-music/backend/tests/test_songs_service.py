"""Lección 7, Paso C: services/songs.py (reglas de negocio, sin HTTP)."""
import ast
import inspect

import pytest
from sqlalchemy import select

from app import models
from app.schemas import SongCreate
from app.services import songs as songs_service


@pytest.fixture
def base(db_factory):
    with db_factory() as db:
        db.add_all([
            models.Genre(id=1, name="Rock"),
            models.Artist(id=1, name="Ana"),
            models.Artist(id=2, name="Beto"),
        ])
        db.commit()


def body(**over):
    data = {
        "title": "Uno", "duration_s": 180, "genre_id": 1,
        "artists": [{"artist_id": 1, "role": "main"}, {"artist_id": 2, "role": "featured"}],
    }
    return SongCreate(**{**data, **over})


def test_create_song_returns_the_full_song(db_factory, base):
    with db_factory() as db:
        song = songs_service.create_song(db, body())
    assert song["id"] == 1 and song["title"] == "Uno"
    assert song["genre"].name == "Rock"
    assert [(a["artist_id"], a["role"]) for a in song["artists"]] == [(1, "main"), (2, "featured")]


def test_unknown_genre_raises_related_not_found(db_factory, base):
    with db_factory() as db:
        with pytest.raises(songs_service.RelatedNotFound, match="99"):
            songs_service.create_song(db, body(genre_id=99))


def test_all_unknown_artists_are_reported_sorted(db_factory, base):
    artists = [{"artist_id": 99, "role": "main"}, {"artist_id": 1, "role": "featured"}, {"artist_id": 77, "role": "writer"}]
    with db_factory() as db:
        with pytest.raises(songs_service.RelatedNotFound, match=r"\[77, 99\]"):
            songs_service.create_song(db, body(artists=artists))


def test_nothing_is_written_when_validation_fails(db_factory, base):
    with db_factory() as db:
        with pytest.raises(songs_service.RelatedNotFound):
            songs_service.create_song(db, body(genre_id=99))
        with pytest.raises(songs_service.RelatedNotFound):
            songs_service.create_song(db, body(artists=[{"artist_id": 99, "role": "main"}]))
    with db_factory() as db:
        assert db.scalars(select(models.Song)).all() == []


def test_service_does_not_know_about_http():
    """La capa de servicio no importa FastAPI: lanza su propia excepción y el router decide el 404."""
    tree = ast.parse(inspect.getsource(songs_service))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
    assert "fastapi" not in imported and "starlette" not in imported

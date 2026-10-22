import copy
import json
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import func, select

seed = pytest.importorskip("app.seed")

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.json"

# Reglas: la canción anidada bajo un artista es suya con rol "main";
# los nombres en "featuring" son colaboradores con rol "featured".
# Los ids van de 1 en adelante, por orden de primera aparición.
CATALOG = {
    "artists": [
        {
            "name": "Ana",
            "songs": [
                {"title": "Uno", "duration_s": 200, "genre": "Rock", "featuring": ["Beto"]},
                {"title": "Dos", "duration_s": 180, "genre": "Pop"},
            ],
        },
        {
            "name": "Beto",
            "songs": [{"title": "Tres", "duration_s": 240, "genre": "Rock"}],
        },
    ]
}

EXPECTED = {
    "genres": [{"id": 1, "name": "Rock"}, {"id": 2, "name": "Pop"}],
    "artists": [{"id": 1, "name": "Ana"}, {"id": 2, "name": "Beto"}],
    "songs": [
        {"id": 1, "title": "Uno", "duration_s": 200, "genre_id": 1},
        {"id": 2, "title": "Dos", "duration_s": 180, "genre_id": 2},
        {"id": 3, "title": "Tres", "duration_s": 240, "genre_id": 1},
    ],
    "song_artists": [
        {"song_id": 1, "artist_id": 1, "role": "main"},
        {"song_id": 1, "artist_id": 2, "role": "featured"},
        {"song_id": 2, "artist_id": 1, "role": "main"},
        {"song_id": 3, "artist_id": 2, "role": "main"},
    ],
}


def load_catalog():
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def real_rows():
    return seed.flatten_catalog(load_catalog())


# ---- aplanar: caso pequeño, con la respuesta exacta ----
def test_flatten_small_catalog():
    assert seed.flatten_catalog(CATALOG) == EXPECTED


def test_flatten_does_not_modify_its_input():
    catalog = load_catalog()
    snapshot = copy.deepcopy(catalog)
    seed.flatten_catalog(catalog)
    assert catalog == snapshot


# ---- aplanar: el seed.json real, con propiedades ----
def test_real_seed_has_enough_data():
    rows = real_rows()
    assert len(rows["genres"]) >= 5
    assert len(rows["artists"]) >= 10
    assert len(rows["songs"]) >= 30


def test_names_are_unique():
    rows = real_rows()
    for table in ("genres", "artists"):
        names = [r["name"] for r in rows[table]]
        assert len(names) == len(set(names)), table


def test_every_song_has_exactly_one_main_artist():
    rows = real_rows()
    mains = Counter(r["song_id"] for r in rows["song_artists"] if r["role"] == "main")
    assert set(mains) == {s["id"] for s in rows["songs"]}
    assert all(n == 1 for n in mains.values())


def test_foreign_keys_point_to_existing_rows():
    rows = real_rows()
    genre_ids = {g["id"] for g in rows["genres"]}
    artist_ids = {a["id"] for a in rows["artists"]}
    song_ids = {s["id"] for s in rows["songs"]}
    assert all(s["genre_id"] in genre_ids for s in rows["songs"])
    assert all(sa["song_id"] in song_ids for sa in rows["song_artists"])
    assert all(sa["artist_id"] in artist_ids for sa in rows["song_artists"])


def test_featured_only_artists_are_created():
    names = {a["name"] for a in real_rows()["artists"]}
    assert {"Rosa Delgado", "Iván Cobre"} <= names


# ---- bonus: volver a anidar ----
def test_titles_by_artist():
    if not hasattr(seed, "titles_by_artist"):
        pytest.skip("bonus: todavía sin escribir")
    rows = seed.flatten_catalog(CATALOG)
    assert seed.titles_by_artist(rows) == {"Ana": ["Uno", "Dos"], "Beto": ["Uno", "Tres"]}


# ---- cargar en la base ----
def test_seed_database_inserts_once(session):
    models = pytest.importorskip("app.models")

    def count(model):
        return session.scalar(select(func.count()).select_from(model))

    assert seed.seed_database(session, CATALOG) is True
    assert count(models.Genre) == 2
    assert count(models.Artist) == 2
    assert count(models.Song) == 3
    assert count(models.SongArtist) == 4

    assert seed.seed_database(session, CATALOG) is False   # idempotente
    assert count(models.Song) == 3

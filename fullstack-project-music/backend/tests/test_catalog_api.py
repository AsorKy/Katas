"""Lección 5: endpoints de lectura de géneros, canciones y artistas contra una base real.

Catálogo de prueba (ids por orden de primera aparición):
  géneros   Rock=1, Pop=2
  artistas  Ana=1, Beto=2
  canciones Uno=1 (Rock, Ana main + Beto featured), Dos=2 (Pop, Ana), Tres=3 (Rock, Beto)

Correr por pasos:
  uv run pytest tests/test_catalog_api.py -k genres -q
  uv run pytest tests/test_catalog_api.py -k "get_song or list_songs" -q
  uv run pytest tests/test_catalog_api.py -k "artist" -q
  uv run pytest tests/test_catalog_api.py -k envelope -q
"""
import pytest

from app import models
from app.seed import seed_database

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


@pytest.fixture
def seeded(db_factory):
    with db_factory() as s:
        assert seed_database(s, CATALOG) is True


def titles(response):
    assert response.status_code == 200
    return [s["title"] for s in response.json()]


def names(response):
    assert response.status_code == 200
    return [a["name"] for a in response.json()]


def add_playlist_with(db_factory, song_ids):
    """Crea un usuario y UNA playlist que contiene las canciones dadas."""
    with db_factory() as s:
        user = models.User(email="x@y.co", password_hash="x")
        s.add(user)
        s.flush()
        playlist = models.Playlist(name="p", owner_id=user.id)
        s.add(playlist)
        s.flush()
        for position, song_id in enumerate(song_ids, start=1):
            s.add(models.PlaylistSong(playlist_id=playlist.id, song_id=song_id, position=position))
        s.commit()


# ---------- Paso 1: géneros ----------
def test_list_genres(client, seeded):
    r = client.get("/genres")
    assert r.status_code == 200
    body = r.json()
    assert [g["name"] for g in body] == ["Rock", "Pop"]
    assert set(body[0]) == {"id", "name", "created_at"}


# ---------- Paso 2: una canción ----------
def test_get_song_with_genre_and_artists(client, seeded):
    r = client.get("/songs/1")
    assert r.status_code == 200
    song = r.json()
    assert song["title"] == "Uno"
    assert song["duration_s"] == 200
    assert song["genre"]["name"] == "Rock"
    assert song["artists"] == [
        {"artist_id": 1, "name": "Ana", "role": "main"},
        {"artist_id": 2, "name": "Beto", "role": "featured"},
    ]


def test_get_song_not_found(client, seeded):
    assert client.get("/songs/999").status_code == 404


# ---------- Paso 3: lista de canciones con filtros ----------
def test_list_songs_default_order(client, seeded):
    assert titles(client.get("/songs")) == ["Uno", "Dos", "Tres"]


def test_list_songs_filter_by_genre(client, seeded):
    assert titles(client.get("/songs", params={"genre_id": 1})) == ["Uno", "Tres"]
    assert titles(client.get("/songs", params={"genre_id": 2})) == ["Dos"]


def test_list_songs_filter_by_artist_includes_featured(client, seeded):
    assert titles(client.get("/songs", params={"artist_id": 1})) == ["Uno", "Dos"]
    assert titles(client.get("/songs", params={"artist_id": 2})) == ["Uno", "Tres"]


def test_filter_by_artist_keeps_all_artists_of_each_song(client, seeded):
    songs = client.get("/songs", params={"artist_id": 2}).json()
    uno = songs[0]
    assert [a["name"] for a in uno["artists"]] == ["Ana", "Beto"]


def test_list_songs_search_by_title(client, seeded):
    assert titles(client.get("/songs", params={"q": "tre"})) == ["Tres"]
    assert titles(client.get("/songs", params={"q": "UNO"})) == ["Uno"]


def test_list_songs_combined_filters(client, seeded):
    assert titles(client.get("/songs", params={"genre_id": 2, "artist_id": 1})) == ["Dos"]
    assert titles(client.get("/songs", params={"genre_id": 2, "artist_id": 2})) == []


def test_list_songs_pagination(client, seeded):
    assert titles(client.get("/songs", params={"limit": 2})) == ["Uno", "Dos"]
    assert titles(client.get("/songs", params={"limit": 2, "offset": 2})) == ["Tres"]


# ---------- Paso 4: artistas ----------
def test_get_artist_with_genres(client, seeded):
    ana = client.get("/artists/1").json()
    assert ana["name"] == "Ana"
    assert ana["genres"] == ["Pop", "Rock"]          # distintos y en orden alfabético
    assert client.get("/artists/2").json()["genres"] == ["Rock"]   # Rock una sola vez


def test_get_artist_not_found(client, seeded):
    assert client.get("/artists/999").status_code == 404


def test_list_artists(client, seeded):
    assert names(client.get("/artists")) == ["Ana", "Beto"]
    assert names(client.get("/artists", params={"q": "an"})) == ["Ana"]
    assert names(client.get("/artists", params={"limit": 1, "offset": 1})) == ["Beto"]
    assert client.get("/artists").json()[0]["genres"] == ["Pop", "Rock"]


def test_list_artists_is_sorted_by_name(client, db_factory):
    # Los ids van por orden de aparición (Zoe=1, Abel=2, Marta=3); la lista, por nombre.
    catalog = {
        "artists": [
            {"name": name, "songs": [{"title": f"Tema de {name}", "duration_s": 100, "genre": "Rock"}]}
            for name in ("Zoe", "Abel", "Marta")
        ]
    }
    with db_factory() as s:
        assert seed_database(s, catalog) is True
    assert names(client.get("/artists")) == ["Abel", "Marta", "Zoe"]
    assert names(client.get("/artists", params={"limit": 2})) == ["Abel", "Marta"]
    assert names(client.get("/artists", params={"limit": 2, "offset": 2})) == ["Zoe"]


def test_artist_songs(client, seeded):
    r = client.get("/artists/2/songs")
    assert titles(r) == ["Uno", "Tres"]
    assert len(r.json()[0]["artists"]) == 2
    assert client.get("/artists/999/songs").status_code == 404


def test_artist_stats_without_playlists(client, seeded):
    r = client.get("/artists/1/stats")
    assert r.status_code == 200
    assert r.json() == {"artist_id": 1, "song_count": 2, "playlist_count": 0}


def test_artist_stats_counts_each_playlist_once(client, seeded, db_factory):
    add_playlist_with(db_factory, [1, 2])    # Uno y Dos (ambas de Ana) en la MISMA playlist
    assert client.get("/artists/1/stats").json() == {
        "artist_id": 1, "song_count": 2, "playlist_count": 1,
    }
    assert client.get("/artists/2/stats").json() == {      # Beto es featured en Uno
        "artist_id": 2, "song_count": 2, "playlist_count": 1,
    }


def test_artist_stats_not_found(client, seeded):
    assert client.get("/artists/999/stats").status_code == 404


# ---------- Paso 5: formato de error unificado ----------
def test_404_uses_error_envelope(client, seeded):
    body = client.get("/songs/999").json()
    assert body["error"]["code"] == "not_found"
    assert "999" in body["error"]["message"]


def test_validation_error_uses_error_envelope(client, seeded):
    r = client.get("/songs", params={"limit": 0})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"

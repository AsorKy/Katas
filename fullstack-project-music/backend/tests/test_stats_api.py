"""pandas: GET /stats/top-genres (público)."""
import pytest

from app import models


@pytest.fixture
def catalog(db_factory):
    """Rock(2 canciones) · Pop · Folk · Jazz, Blues, Ska y Soul sin canciones; 2 playlists."""
    with db_factory() as db:
        db.add(models.User(id=1, email="ana@example.com", password_hash="x"))
        db.add_all([models.Genre(id=i, name=n) for i, n in
                    [(1, "Rock"), (2, "Pop"), (3, "Jazz"), (4, "Folk"), (5, "Blues"), (6, "Ska"), (7, "Soul")]])
        db.add(models.Artist(id=1, name="Ana"))
        db.commit()
        db.add_all([
            models.Song(id=1, title="S1", duration_s=100, genre_id=1),
            models.Song(id=2, title="S2", duration_s=200, genre_id=1),
            models.Song(id=3, title="S3", duration_s=300, genre_id=2),
            models.Song(id=4, title="S4", duration_s=60, genre_id=4),
        ])
        db.add_all([models.Playlist(id=1, name="P1", owner_id=1), models.Playlist(id=2, name="P2", owner_id=1)])
        db.commit()
        db.add_all([
            models.PlaylistSong(playlist_id=1, song_id=1, position=1),
            models.PlaylistSong(playlist_id=1, song_id=2, position=2),
            models.PlaylistSong(playlist_id=1, song_id=3, position=3),
            models.PlaylistSong(playlist_id=1, song_id=4, position=4),
            models.PlaylistSong(playlist_id=2, song_id=1, position=1),
        ])
        db.commit()


def test_top_genres_ranking(client, catalog):
    r = client.get("/stats/top-genres", params={"limit": 10})
    assert r.status_code == 200
    assert r.json() == [
        {"genre_id": 1, "name": "Rock", "song_count": 2, "playlist_count": 2, "avg_duration_s": 150.0},
        {"genre_id": 4, "name": "Folk", "song_count": 1, "playlist_count": 1, "avg_duration_s": 60.0},
        {"genre_id": 2, "name": "Pop", "song_count": 1, "playlist_count": 1, "avg_duration_s": 300.0},
        {"genre_id": 5, "name": "Blues", "song_count": 0, "playlist_count": 0, "avg_duration_s": 0.0},
        {"genre_id": 3, "name": "Jazz", "song_count": 0, "playlist_count": 0, "avg_duration_s": 0.0},
        {"genre_id": 6, "name": "Ska", "song_count": 0, "playlist_count": 0, "avg_duration_s": 0.0},
        {"genre_id": 7, "name": "Soul", "song_count": 0, "playlist_count": 0, "avg_duration_s": 0.0},
    ]


def test_top_genres_limit(client, catalog):
    names = [g["name"] for g in client.get("/stats/top-genres", params={"limit": 2}).json()]
    assert names == ["Rock", "Folk"]


def test_top_genres_default_limit_is_5(client, catalog):
    body = client.get("/stats/top-genres").json()
    assert len(body) == 5 and body[-1]["name"] == "Jazz"


@pytest.mark.parametrize("limit", [0, 51, -1])
def test_top_genres_limit_out_of_range_is_422(client, catalog, limit):
    r = client.get("/stats/top-genres", params={"limit": limit})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_top_genres_empty_database_is_200_empty_list(client):
    r = client.get("/stats/top-genres")
    assert r.status_code == 200 and r.json() == []

"""NumPy: GET /songs/{song_id}/similar (público)."""
import pytest

from app import models


@pytest.fixture
def library(db_factory):
    """
    S1 Rock  [Ana main, Beto featured]      S4 Rock [Caro]
    S2 Rock  [Ana]                          S5 Pop  [Caro]
    S3 Pop   [Ana]                          S6 Jazz [Dina]   (aislada)
    """
    with db_factory() as db:
        db.add_all([models.Genre(id=1, name="Rock"), models.Genre(id=2, name="Pop"), models.Genre(id=3, name="Jazz")])
        db.add_all([models.Artist(id=i, name=n) for i, n in [(1, "Ana"), (2, "Beto"), (3, "Caro"), (4, "Dina")]])
        db.commit()
        genres = {1: 1, 2: 1, 3: 2, 4: 1, 5: 2, 6: 3}
        db.add_all([models.Song(id=i, title=f"S{i}", duration_s=100 + i, genre_id=g) for i, g in genres.items()])
        db.commit()
        db.add_all([
            models.SongArtist(song_id=1, artist_id=1, role="main"),
            models.SongArtist(song_id=1, artist_id=2, role="featured"),
            models.SongArtist(song_id=2, artist_id=1, role="main"),
            models.SongArtist(song_id=3, artist_id=1, role="main"),
            models.SongArtist(song_id=4, artist_id=3, role="main"),
            models.SongArtist(song_id=5, artist_id=3, role="main"),
            models.SongArtist(song_id=6, artist_id=4, role="main"),
        ])
        db.commit()


def item(song_id, score):
    return {"song_id": song_id, "title": f"S{song_id}", "score": score}


def test_similar_ranks_by_shared_genre_and_artists(client, library):
    r = client.get("/songs/2/similar")
    assert r.status_code == 200
    # S1 comparte género y artista (2/√6); S3 solo artista y S4 solo género (1/2, empate: por id)
    assert r.json() == [item(1, 0.8165), item(3, 0.5), item(4, 0.5)]


def test_similar_with_featured_artist(client, library):
    assert client.get("/songs/1/similar").json() == [item(2, 0.8165), item(3, 0.4082), item(4, 0.4082)]


def test_similar_limit(client, library):
    assert client.get("/songs/2/similar", params={"limit": 1}).json() == [item(1, 0.8165)]


def test_similar_excludes_itself_and_zero_scores(client, library):
    ids = [s["song_id"] for s in client.get("/songs/5/similar").json()]
    assert ids == [3, 4]


def test_similar_isolated_song_is_200_empty_list(client, library):
    r = client.get("/songs/6/similar")
    assert r.status_code == 200 and r.json() == []


def test_similar_unknown_song_is_404(client, library):
    r = client.get("/songs/99/similar")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found" and "99" in r.json()["error"]["message"]


@pytest.mark.parametrize("limit", [0, 51])
def test_similar_limit_out_of_range_is_422(client, library, limit):
    assert client.get("/songs/2/similar", params={"limit": limit}).status_code == 422

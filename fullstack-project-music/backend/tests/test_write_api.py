"""Lección 7: escrituras protegidas (POST /artists y POST /songs)."""
import pytest

from app import models

CREDS = {"email": "ana@example.com", "password": "supersecret1"}

SONG = {
    "title": "Uno",
    "duration_s": 180,
    "genre_id": 1,
    "artists": [{"artist_id": 1, "role": "main"}, {"artist_id": 2, "role": "featured"}],
}


def auth_header(client):
    client.post("/auth/register", json=CREDS)
    token = client.post("/auth/login", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def base(db_factory):
    """Dos géneros y dos artistas ya existentes (el contrato no tiene POST /genres)."""
    with db_factory() as db:
        db.add_all([
            models.Genre(id=1, name="Rock"), models.Genre(id=2, name="Pop"),
            models.Artist(id=1, name="Ana"), models.Artist(id=2, name="Beto"),
        ])
        db.commit()


# ---------- POST /artists ----------
def test_create_artist_requires_auth(client):
    r = client.post("/artists", json={"name": "Zoe"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_create_artist(client):
    r = client.post("/artists", json={"name": "Zoe"}, headers=auth_header(client))
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1 and body["name"] == "Zoe"
    assert body["genres"] == []                 # sin canciones todavía
    assert "created_at" in body


def test_created_artist_is_visible_in_reads(client):
    h = auth_header(client)
    new_id = client.post("/artists", json={"name": "Zoe"}, headers=h).json()["id"]
    assert client.get(f"/artists/{new_id}").json()["name"] == "Zoe"
    assert [a["name"] for a in client.get("/artists").json()] == ["Zoe"]


def test_create_artist_duplicate_name_is_409(client):
    h = auth_header(client)
    client.post("/artists", json={"name": "Zoe"}, headers=h)
    r = client.post("/artists", json={"name": "Zoe"}, headers=h)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_create_artist_empty_name_is_422(client):
    r = client.post("/artists", json={"name": ""}, headers=auth_header(client))
    assert r.status_code == 422


# ---------- POST /songs ----------
def test_create_song_requires_auth(client, base):
    r = client.post("/songs", json=SONG)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_create_song(client, base):
    r = client.post("/songs", json=SONG, headers=auth_header(client))
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1 and body["title"] == "Uno" and body["duration_s"] == 180
    assert body["genre"]["name"] == "Rock"
    assert body["artists"] == [
        {"artist_id": 1, "name": "Ana", "role": "main"},
        {"artist_id": 2, "name": "Beto", "role": "featured"},
    ]


def test_created_song_is_visible_in_reads(client, base):
    created = client.post("/songs", json=SONG, headers=auth_header(client)).json()
    assert client.get("/songs/1").json() == created
    assert [s["title"] for s in client.get("/artists/2/songs").json()] == ["Uno"]  # el featured también


def test_create_song_unknown_genre_is_404(client, base):
    r = client.post("/songs", json={**SONG, "genre_id": 99}, headers=auth_header(client))
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
    assert "99" in r.json()["error"]["message"]


def test_create_song_unknown_artist_is_404(client, base):
    bad = {**SONG, "artists": [{"artist_id": 1, "role": "main"}, {"artist_id": 77, "role": "featured"}]}
    r = client.post("/songs", json=bad, headers=auth_header(client))
    assert r.status_code == 404
    assert "77" in r.json()["error"]["message"]


def test_failed_create_leaves_no_song_behind(client, base):
    h = auth_header(client)
    bad = {**SONG, "artists": [{"artist_id": 1, "role": "main"}, {"artist_id": 99, "role": "featured"}]}
    assert client.post("/songs", json=bad, headers=h).status_code == 404
    assert client.get("/songs").json() == []


@pytest.mark.parametrize(
    "change",
    [
        {"artists": []},
        {"artists": [{"artist_id": 1, "role": "dj"}]},
        {"duration_s": 0},
        {"title": ""},
        {"artists": [{"artist_id": 1, "role": "main"}, {"artist_id": 1, "role": "writer"}]},
    ],
    ids=["no-artists", "bad-role", "zero-duration", "empty-title", "duplicate-artist"],
)
def test_create_song_invalid_body_is_422(client, base, change):
    r = client.post("/songs", json={**SONG, **change}, headers=auth_header(client))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"

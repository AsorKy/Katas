"""Lección 8: playlists (dueño, orden de canciones, 404 para ajenas, 409 duplicada)."""
import pytest

from app import models

PASSWORD = "supersecret1"


def auth_header(client, email="ana@example.com"):
    client.post("/auth/register", json={"email": email, "password": PASSWORD})
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def songs(db_factory):
    """Canciones S1..S4 (todas de Ana; S1 con Beto como featured)."""
    with db_factory() as db:
        db.add_all([models.Genre(id=1, name="Rock"), models.Artist(id=1, name="Ana"), models.Artist(id=2, name="Beto")])
        db.commit()
        db.add_all([models.Song(id=i, title=f"S{i}", duration_s=100 + i, genre_id=1) for i in range(1, 5)])
        db.commit()
        db.add_all([models.SongArtist(song_id=i, artist_id=1, role="main") for i in range(1, 5)])
        db.add(models.SongArtist(song_id=1, artist_id=2, role="featured"))
        db.commit()


def make_playlist(client, headers, name="Mix"):
    return client.post("/playlists", json={"name": name}, headers=headers).json()["id"]


def add(client, headers, playlist_id, song_id):
    return client.post(f"/playlists/{playlist_id}/songs", json={"song_id": song_id}, headers=headers)


def titles(response):
    return [s["title"] for s in response.json()["songs"]]


# ================= Paso 1: crear y listar las mías =================
def test_create_playlist_requires_auth(client):
    r = client.post("/playlists", json={"name": "Mix"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_create_playlist(client):
    r = client.post("/playlists", json={"name": "Mix"}, headers=auth_header(client))
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1 and body["name"] == "Mix" and "created_at" in body


def test_create_playlist_empty_name_is_422(client):
    r = client.post("/playlists", json={"name": ""}, headers=auth_header(client))
    assert r.status_code == 422


def test_list_playlists_requires_auth(client):
    assert client.get("/playlists").status_code == 401


def test_list_playlists_empty(client):
    assert client.get("/playlists", headers=auth_header(client)).json() == []


def test_list_playlists_returns_only_mine(client):
    ana, beto = auth_header(client, "ana@example.com"), auth_header(client, "beto@example.com")
    make_playlist(client, ana, "A1")
    make_playlist(client, beto, "B1")
    make_playlist(client, ana, "A2")
    assert [p["name"] for p in client.get("/playlists", headers=ana).json()] == ["A1", "A2"]
    assert [p["name"] for p in client.get("/playlists", headers=beto).json()] == ["B1"]


# ================= Paso 2: detalle (solo del dueño) =================
def test_playlist_detail_requires_auth(client):
    assert client.get("/playlists/1").status_code == 401


def test_playlist_detail_empty(client):
    h = auth_header(client)
    pid = make_playlist(client, h)
    r = client.get(f"/playlists/{pid}", headers=h)
    assert r.status_code == 200
    assert r.json() == {"id": pid, "name": "Mix", "songs": []}


def test_playlist_detail_of_unknown_is_404(client):
    r = client.get("/playlists/99", headers=auth_header(client))
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_playlist_detail_of_someone_else_is_404(client):
    ana, beto = auth_header(client, "ana@example.com"), auth_header(client, "beto@example.com")
    pid = make_playlist(client, ana)
    r = client.get(f"/playlists/{pid}", headers=beto)
    assert r.status_code == 404                      # 404 y no 403: no confirma que exista
    assert r.json()["error"]["code"] == "not_found"


# ================= Paso 3: añadir canciones =================
def test_add_song_requires_auth(client):
    assert client.post("/playlists/1/songs", json={"song_id": 1}).status_code == 401


def test_add_song_returns_detail_with_full_song(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    r = add(client, h, pid, 1)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == pid and body["name"] == "Mix"
    song = body["songs"][0]
    assert song["title"] == "S1" and song["genre"]["name"] == "Rock"
    assert song["artists"] == [
        {"artist_id": 1, "name": "Ana", "role": "main"},
        {"artist_id": 2, "name": "Beto", "role": "featured"},
    ]


def test_add_song_keeps_position_order_not_id_order(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    add(client, h, pid, 3)
    add(client, h, pid, 1)
    r = add(client, h, pid, 4)
    assert titles(r) == ["S3", "S1", "S4"]
    assert titles(client.get(f"/playlists/{pid}", headers=h)) == ["S3", "S1", "S4"]


def test_add_song_twice_is_409(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    add(client, h, pid, 1)
    r = add(client, h, pid, 1)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"
    assert titles(client.get(f"/playlists/{pid}", headers=h)) == ["S1"]


def test_add_song_unknown_song_is_404(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    r = add(client, h, pid, 99)
    assert r.status_code == 404 and "99" in r.json()["error"]["message"]


def test_add_song_to_unknown_playlist_is_404(client, songs):
    assert add(client, auth_header(client), 99, 1).status_code == 404


def test_add_song_to_someone_elses_playlist_is_404(client, songs):
    ana, beto = auth_header(client, "ana@example.com"), auth_header(client, "beto@example.com")
    pid = make_playlist(client, ana)
    assert add(client, beto, pid, 1).status_code == 404
    assert titles(client.get(f"/playlists/{pid}", headers=ana)) == []      # no se escribió nada


def test_add_song_missing_song_id_is_422(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    assert client.post(f"/playlists/{pid}/songs", json={}, headers=h).status_code == 422


def test_artist_playlist_count_sums_all_users(client, songs):
    ana, beto = auth_header(client, "ana@example.com"), auth_header(client, "beto@example.com")
    p1, p2 = make_playlist(client, ana), make_playlist(client, beto)
    add(client, ana, p1, 1)
    add(client, ana, p1, 2)          # dos canciones de Ana en la MISMA playlist: cuenta una vez
    add(client, beto, p2, 3)
    assert client.get("/artists/1/stats").json()["playlist_count"] == 2


# ================= Paso 4: quitar canciones =================
def test_remove_song_requires_auth(client):
    assert client.delete("/playlists/1/songs/1").status_code == 401


def test_remove_song(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    add(client, h, pid, 1)
    add(client, h, pid, 2)
    r = client.delete(f"/playlists/{pid}/songs/1", headers=h)
    assert r.status_code == 204 and r.content == b""
    assert titles(client.get(f"/playlists/{pid}", headers=h)) == ["S2"]


def test_remove_song_not_in_playlist_is_404(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    add(client, h, pid, 1)
    r = client.delete(f"/playlists/{pid}/songs/3", headers=h)
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_remove_song_from_someone_elses_playlist_is_404(client, songs):
    ana, beto = auth_header(client, "ana@example.com"), auth_header(client, "beto@example.com")
    pid = make_playlist(client, ana)
    add(client, ana, pid, 1)
    assert client.delete(f"/playlists/{pid}/songs/1", headers=beto).status_code == 404
    assert titles(client.get(f"/playlists/{pid}", headers=ana)) == ["S1"]


def test_remove_then_add_appends_at_the_end(client, songs):
    h = auth_header(client)
    pid = make_playlist(client, h)
    for song_id in (3, 1, 4):
        add(client, h, pid, song_id)
    client.delete(f"/playlists/{pid}/songs/1", headers=h)
    r = add(client, h, pid, 2)
    assert titles(r) == ["S3", "S4", "S2"]

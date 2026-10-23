from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

EXPECTED_ROUTES = {
    ("post", "/auth/register"),
    ("post", "/auth/login"),
    ("get", "/me"),
    ("get", "/genres"),
    ("post", "/artists"),
    ("get", "/artists"),
    ("get", "/artists/{artist_id}"),
    ("get", "/artists/{artist_id}/songs"),
    ("get", "/artists/{artist_id}/stats"),
    ("post", "/songs"),
    ("get", "/songs"),
    ("get", "/songs/{song_id}"),
    ("post", "/playlists"),
    ("get", "/playlists"),
    ("get", "/playlists/{playlist_id}"),
    ("post", "/playlists/{playlist_id}/songs"),
    ("delete", "/playlists/{playlist_id}/songs/{song_id}"),
    ("get", "/health"),
}

SUCCESS_CODES = {
    ("post", "/auth/register"): "201",
    ("post", "/auth/login"): "200",
    ("post", "/artists"): "201",
    ("post", "/songs"): "201",
    ("post", "/playlists"): "201",
    ("post", "/playlists/{playlist_id}/songs"): "201",
    ("delete", "/playlists/{playlist_id}/songs/{song_id}"): "204",
}


def openapi_paths():
    return client.get("/openapi.json").json()["paths"]


def test_all_routes_exist():
    actual = {(m, p) for p, ops in openapi_paths().items() for m in ops}
    assert EXPECTED_ROUTES <= actual, f"faltan: {sorted(EXPECTED_ROUTES - actual)}"


def test_declared_success_codes():
    paths = openapi_paths()
    for (method, path), code in SUCCESS_CODES.items():
        responses = paths.get(path, {}).get(method, {}).get("responses", {})
        assert code in responses, f"{method.upper()} {path} debe declarar {code}"


def test_stubs_answer_501():
    # Pendientes de las lecciones de auth y playlists. Borrar este test al terminarlas.
    assert client.get("/playlists").status_code == 501
    assert client.get("/me").status_code == 501

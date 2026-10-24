"""Lección 9: CORS. El navegador (React en :5173) debe poder llamar a la API (:8000)."""

ORIGIN = "http://localhost:5173"


def test_preflight_allows_frontend_origin_and_headers(client):
    r = client.options(
        "/auth/login",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGIN
    allowed = r.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed and "content-type" in allowed


def test_normal_request_carries_cors_header(client):
    r = client.get("/songs", headers={"Origin": ORIGIN})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ORIGIN


def test_error_responses_also_carry_cors_header(client):
    # si el 401 no lleva la cabecera, el navegador lo oculta y React ve un "Network Error"
    r = client.get("/me", headers={"Origin": ORIGIN})
    assert r.status_code == 401
    assert r.headers["access-control-allow-origin"] == ORIGIN


def test_unknown_origin_gets_no_cors_header(client):
    r = client.get("/songs", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers

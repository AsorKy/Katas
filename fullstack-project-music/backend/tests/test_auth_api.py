"""Lección 6: autenticación (registro, login, JWT, /me)."""
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select

from app import models
from app.config import settings

CREDS = {"email": "ana@example.com", "password": "supersecret1"}


def register(client, **over):
    return client.post("/auth/register", json={**CREDS, **over})


def login(client, **over):
    return client.post("/auth/login", json={**CREDS, **over})


def auth_header(client):
    register(client)
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_token(sub, delta=timedelta(minutes=5), key=None):
    exp = datetime.now(timezone.utc) + delta
    return jwt.encode({"sub": str(sub), "exp": exp}, key or settings.secret_key, algorithm=settings.algorithm)


# ---------- registro ----------
def test_register_returns_user_without_password(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1 and body["email"] == CREDS["email"]
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_is_409(client):
    register(client)
    r = register(client, password="otra-clave-123")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_register_short_password_is_422(client):
    assert register(client, password="corta").status_code == 422


def test_password_is_stored_hashed(client, db_factory):
    register(client)
    with db_factory() as db:
        user = db.scalar(select(models.User))
    assert user.password_hash != CREDS["password"]
    assert user.password_hash.startswith("$argon2")


# ---------- login ----------
def test_login_returns_bearer_token(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_is_401(client):
    register(client)
    r = login(client, password="no-es-la-clave")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_login_unknown_email_gives_same_error_as_wrong_password(client):
    """Mismo mensaje en ambos casos: no revela qué correos están registrados."""
    register(client)
    wrong_pw = login(client, password="no-es-la-clave")
    unknown = login(client, email="nadie@example.com")
    assert unknown.status_code == 401
    assert unknown.json() == wrong_pw.json()


def test_token_carries_user_id_and_expiry(client):
    register(client)
    token = login(client).json()["access_token"]
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "1"
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


# ---------- /me ----------
def test_me_with_valid_token(client):
    r = client.get("/me", headers=auth_header(client))
    assert r.status_code == 200
    assert r.json()["email"] == CREDS["email"]


def test_me_without_token_is_401(client):
    r = client.get("/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


def test_me_with_garbage_token_is_401(client):
    r = client.get("/me", headers={"Authorization": "Bearer esto.no.es.un.jwt"})
    assert r.status_code == 401


def test_me_with_expired_token_is_401(client):
    register(client)
    expired = make_token(1, delta=timedelta(minutes=-1))
    assert client.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_me_with_token_signed_by_someone_else_is_401(client):
    register(client)
    forged = make_token(1, key="otra-clave-secreta-de-32-bytes-o-mas!!")
    assert client.get("/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_me_with_token_of_nonexistent_user_is_401(client):
    ghost = make_token(999)
    assert client.get("/me", headers={"Authorization": f"Bearer {ghost}"}).status_code == 401

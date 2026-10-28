"""Reto 3 (20 min) · API de tracks con FastAPI + SQLAlchemy 2 + Pydantic v2

Ejecútalo con el Python del venv del backend (ya trae FastAPI, SQLAlchemy y el cliente de pruebas):
    fullstack-project-music/backend/.venv/bin/python python-backend/diagnostico-1/03-tracks-api.py
Está resuelto cuando termina sin AssertionError.

Reglas del drill: a mano, sin IA, sin copiar de tu proyecto. Cronometra.

Qué hay que construir (entre las dos líneas marcadas):
  - Modelo Track: id (clave primaria), title (único), artist, duration_s.
  - Esquemas de entrada y de salida separados (Pydantic v2).
  - Un router con prefijo /tracks y estos endpoints:
      POST   /tracks        body {title, artist, duration_s}
                            -> 201 y el track creado {id, title, artist, duration_s}
                            -> 422 si title o artist están vacíos, o duration_s <= 0
                            -> 409 si ya existe un track con ese title
      GET    /tracks        filtros opcionales: artist (igual exacto), min_duration (>=)
                            paginación: limit (por defecto 10, entre 1 y 50), offset (>= 0)
                            -> lista ordenada por id; parámetros fuera de rango -> 422
      GET    /tracks/{id}   -> 200, o 404 si no existe
      DELETE /tracks/{id}   -> 204 sin cuerpo, o 404 si no existe
  - Un objeto `app` (FastAPI) con el router incluido. Usa Depends(get_db).
"""
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query  # noqa: F401
from pydantic import BaseModel, ConfigDict, Field  # noqa: F401
from sqlalchemy import create_engine, select  # noqa: F401
from sqlalchemy.exc import IntegrityError  # noqa: F401
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker  # noqa: F401
from sqlalchemy.pool import StaticPool

# ---------------- Andamiaje (ya hecho, no lo toques) ----------------
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db


# ---------------- TU CÓDIGO (desde aquí) ----------------





# ---------------- TU CÓDIGO (hasta aquí) ----------------

# --- Pruebas (no las edites) ---
from fastapi.testclient import TestClient  # noqa: E402

Base.metadata.create_all(engine)
c = TestClient(app)


def ids(resp):
    assert resp.status_code == 200, resp.text
    return [t["id"] for t in resp.json()]


r = c.post("/tracks", json={"title": "Uno", "artist": "Ana", "duration_s": 180})
assert r.status_code == 201, r.text
assert r.json() == {"id": 1, "title": "Uno", "artist": "Ana", "duration_s": 180}

assert c.post("/tracks", json={"title": "Uno", "artist": "Beto", "duration_s": 100}).status_code == 409
assert c.post("/tracks", json={"title": "", "artist": "Ana", "duration_s": 10}).status_code == 422
assert c.post("/tracks", json={"title": "X", "artist": "", "duration_s": 10}).status_code == 422
assert c.post("/tracks", json={"title": "X", "artist": "Ana", "duration_s": 0}).status_code == 422
assert c.post("/tracks", json={"title": "X", "artist": "Ana"}).status_code == 422

for t, a, d in [("Dos", "Ana", 200), ("Tres", "Beto", 90), ("Cuatro", "Ana", 300)]:
    assert c.post("/tracks", json={"title": t, "artist": a, "duration_s": d}).status_code == 201

assert ids(c.get("/tracks")) == [1, 2, 3, 4]
assert ids(c.get("/tracks", params={"artist": "Ana"})) == [1, 2, 4]
assert ids(c.get("/tracks", params={"min_duration": 200})) == [2, 4]
assert ids(c.get("/tracks", params={"artist": "Ana", "min_duration": 250})) == [4]
assert ids(c.get("/tracks", params={"limit": 2})) == [1, 2]
assert ids(c.get("/tracks", params={"limit": 2, "offset": 2})) == [3, 4]
assert c.get("/tracks", params={"limit": 0}).status_code == 422
assert c.get("/tracks", params={"limit": 51}).status_code == 422
assert c.get("/tracks", params={"offset": -1}).status_code == 422

assert c.get("/tracks/2").json()["title"] == "Dos"
assert c.get("/tracks/999").status_code == 404

r = c.delete("/tracks/2")
assert r.status_code == 204 and r.content == b""
assert c.get("/tracks/2").status_code == 404
assert c.delete("/tracks/2").status_code == 404
assert ids(c.get("/tracks")) == [1, 3, 4]

assert c.post("/tracks", json={"title": "Cinco", "artist": "Ana", "duration_s": 60}).status_code == 201
print("Reto 3: OK")

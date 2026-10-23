# Music API · mini proyecto full stack

API de música (usuarios, artistas, canciones, géneros y playlists) con backend en Python y frontend en React.
Proyecto de práctica para entrenar la codificación a mano: **contrato primero**, después datos, autenticación y consultas.

## Alcance

**Dentro:** registro y login, canciones con uno o varios artistas, listado con filtros, playlists,
canciones en las que participa un artista y en cuántas playlists aparece.

**Fuera (por ahora):** subida de audio real, Redis, Alembic, Compose, pagos.

"Cargar una canción" significa registrar su **metadato** (título, duración, género, artistas).
Subir el archivo de audio queda como extra, detrás de un adaptador `Storage`.

## Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 (síncrono) · SQLite · JWT (PyJWT) ·
hash de contraseñas con Argon2 (pwdlib) · pytest · uv · React (Vite) · un solo Dockerfile al final.

La URL de la base sale de la variable `DATABASE_URL`, así que pasar a Postgres es cambiar una línea.

## Modelo de datos (7 tablas)

```
users 1─N playlists 1─N playlist_songs N─1 songs
artists N─M songs        (tabla song_artists, con role = main | featured)
genres 1─N songs         (un género por canción)
```

| Tabla | Columnas |
|---|---|
| `users` | id, email (único), password_hash, created_at |
| `artists` | id, name |
| `genres` | id, name (único) |
| `songs` | id, title, duration_s, genre_id → genres, created_at |
| `song_artists` | song_id → songs, artist_id → artists, role (`main` / `featured` / `producer` / `writer`). PK (song_id, artist_id) |
| `playlists` | id, name, owner_id → users, created_at |
| `playlist_songs` | playlist_id → playlists, song_id → songs, position, added_at. PK (playlist_id, song_id) |

Regla de negocio: cada canción tiene **exactamente un** artista `main`.

## Contrato de la API

Autenticación con JWT en la cabecera `Authorization: Bearer <token>`.
Los parámetros de ruta se llaman `{artist_id}`, `{song_id}` y `{playlist_id}`.

| Método y ruta | Auth | Cuerpo o query | Éxito | Errores |
|---|---|---|---|---|
| `POST /auth/register` | no | `UserCreate` | 201 `UserOut` | 409 correo existe, 422 |
| `POST /auth/login` | no | `UserCreate` | 200 `Token` | 401 |
| `GET /me` | sí | — | 200 `UserOut` | 401 |
| `GET /genres` | no | — | 200 `list[GenreOut]` | — |
| `POST /artists` | sí | `ArtistsCreate` | 201 `ArtistsOut` | 401, 422 |
| `GET /artists` | no | `q`, `limit`, `offset` | 200 `list[ArtistsOut]` | — |
| `GET /artists/{artist_id}` | no | — | 200 `ArtistsOut` | 404 |
| `GET /artists/{artist_id}/songs` | no | — | 200 `list[SongsOut]` | 404 |
| `GET /artists/{artist_id}/stats` | no | — | 200 `ArtistStats` | 404 |
| `POST /songs` | sí | `SongCreate` | 201 `SongsOut` | 401, 404 artista o género, 422 |
| `GET /songs` | no | `genre_id`, `artist_id`, `q`, `limit`, `offset` | 200 `list[SongsOut]` | — |
| `GET /songs/{song_id}` | no | — | 200 `SongsOut` | 404 |
| `POST /playlists` | sí | `PlaylistsCreate` | 201 `PlaylistOut` | 401, 422 |
| `GET /playlists` | sí | — | 200 `list[PlaylistOut]` (las mías) | 401 |
| `GET /playlists/{playlist_id}` | sí, dueño | — | 200 `PlaylistDetail` | 401, 404 |
| `POST /playlists/{playlist_id}/songs` | sí, dueño | `PlaylistAddSong` | 201 `PlaylistDetail` | 401, 404, 409 ya está |
| `DELETE /playlists/{playlist_id}/songs/{song_id}` | sí, dueño | — | 204 | 401, 404 |
| `GET /health` | no | — | 200 `{"status": "ok"}` | — |

**Fase 2:** `GET /stats/top-genres` (pandas) y `GET /songs/{song_id}/similar` (NumPy).

Paginación: `limit` (por defecto 20, máximo 100) y `offset` (por defecto 0).
`GET /artists` ordena por nombre; las demás listas, por id.

### Schemas

| Schema | Campos |
|---|---|
| `UserCreate` | `email`, `password` (mínimo 8 caracteres) |
| `UserOut` | `id`, `email`, `created_at` |
| `Token` | `access_token`, `token_type` (`"bearer"`) |
| `GenreOut` | `id`, `name`, `created_at` |
| `ArtistsCreate` | `name` (no vacío) |
| `ArtistsOut` | `id`, `name`, `genres: list[str]` (calculado), `created_at` |
| `SongArtistIn` | `artist_id`, `role` (`main`, `featured`, `producer` o `writer`) |
| `SongCreate` | `title`, `duration_s` (> 0), `genre_id`, `artists: list[SongArtistIn]` (al menos uno) |
| `SongsArtistOut` | `artist_id`, `name`, `role` |
| `SongsOut` | `id`, `title`, `duration_s`, `genre: GenreOut`, `created_at`, `artists: list[SongsArtistOut]` |
| `ArtistStats` | `artist_id`, `song_count`, `playlist_count` |
| `PlaylistsCreate` | `name` (no vacío) |
| `PlaylistOut` | `id`, `name`, `created_at` |
| `PlaylistDetail` | `id`, `name`, `songs: list[SongsOut]` |
| `PlaylistAddSong` | `song_id` |

Notas sobre los schemas:
- Los nombres van en plural (`ArtistsOut`, `SongsOut`, `PlaylistsCreate`…) para coincidir con el código.
- `ArtistsOut.genres` es un dato **calculado**: los géneros distintos de las canciones del artista. No se guarda en la tabla `artists` y no se envía al crear (`ArtistsCreate` solo lleva `name`).
- Los campos `created_at` son `datetime` y salen en JSON como texto ISO 8601.

### Reglas transversales

- Todos los errores salen con el mismo formato, también el 500:
  `{"error": {"code": "not_found", "message": "Song 7 not found"}}`.
  Códigos: `validation_error`, `unauthorized`, `not_found`, `conflict`, `internal_error`.
- `password_hash` nunca sale en una respuesta.
- Las contraseñas se guardan con hash (Argon2), jamás en claro.
- Una playlist ajena responde **404**, no 403, para no confirmar que existe.
- El `playlist_count` de un artista es un agregado: cuenta playlists sin revelar de quién son.

## Cómo correr

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload     # http://localhost:8000/docs
uv run pytest -q
```

## Estructura

```
fullstack-project-music/
  backend/
    app/        main.py · schemas.py · routers/ · services/ · repositories/
    tests/
    data/       base SQLite y semilla
  frontend/
```

## Orden de construcción

- [x] Entorno con uv y `/health`
- [x] Contrato: schemas y rutas que responden 501 (`tests/test_contract.py`)
- [x] Modelos, base de datos y semilla (aplanar el JSON anidado)
- [ ] Autenticación
- [ ] Canciones y artistas, con las consultas SQL
- [ ] Playlists
- [ ] pandas: `/stats/top-genres` · NumPy: `/songs/{id}/similar`
- [ ] React: `SongList`, `LoginForm`
- [ ] Dockerfile

## Criterio de "hecho"

Los tests pasan, `/docs` muestra el contrato, un script con `curl` recorre el flujo completo
(registro, login, crear canción, crear playlist, añadir canción) y `docker run` levanta la API.

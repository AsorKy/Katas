---
tags: [fullstack-project-music, leccion, hecha]
leccion: 5
estado: hecha
---

# Lección 5 · Canciones y artistas, con sus consultas SQL

> **Objetivo:** convertir los stubs 501 del catálogo en endpoints reales: lecturas (`GET /genres`, `/songs`, `/artists` y derivados), formato de error unificado y, después de autenticar, las escrituras protegidas (`POST /artists`, `POST /songs`) con una capa de servicio. Es la lección donde aparece el patrón **router → servicio → repositorio** que reutilizan las siguientes.

## 0. Dónde encaja

- Es el **quinto de los siete pasos de construcción** (entorno → contrato → modelos → autenticación → **canciones y artistas** → playlists → Dockerfile), pero la lección se hizo **en dos mitades separadas por la autenticación**:
  1. **Parte A (sección 2A):** lectura del catálogo y sobre de errores. Se hizo **antes** de auth (22–23 oct), porque los `GET` son públicos y enseñan el patrón `Depends(get_db)` → repositorio → modelo → schema que luego reutiliza `current_user`.
  2. **[[lesson-4]] (autenticación):** `security.py`, `depends.py`, register/login/me.
  3. **Parte B (sección 2B):** `POST /artists` y `POST /songs`, que necesitan `current_user`, y la capa `services/` (23–24 oct).
- Viene después de [[lesson-3]] (modelos, base y semilla: sin datos en la base no hay nada que consultar) y de [[lesson-2]] (contrato: las rutas ya existían como stubs 501 y los tests de contrato fijaban sus códigos).
- La usan: [[lesson-6]] (playlists reutiliza `current_user`, el patrón de servicio y las excepciones propias), [[lesson-8]] (pandas y NumPy leen de estos repositorios) y [[lesson-9]] (React consume `GET /songs`).
- Cubre la parte central del README: las filas del contrato de `/genres`, `/artists…`, `/songs…` y el criterio "los tests pasan, `/docs` muestra el contrato".
- Es también **el SQL que se pide en entrevista**: joins entre canciones, artistas y rol; conteos por artista; filtros opcionales; paginación; N+1.

## 1. Qué se hizo (resumen)

- **Parte A.** El tutor entregó los tests (19 rojos al principio) y el usuario escribió el código paso a paso: `created_at` en `genres` (paso 0), `GET /genres`, `GET /songs/{id}`, `GET /artists/{id}`, `GET /artists`, `GET /artists/{id}/stats`, `GET /songs` con filtros y paginación, y `GET /artists/{id}/songs`. Se midió el problema **N+1** (25 consultas frente a 2 con `IN`) y se montó el **sobre de errores unificado** con handlers en `main.py`. La suite cerró en **46 passed, 1 skipped**.
- **Parte B.** Con auth hecha: `POST /artists` (201/401/409/422) y `POST /songs` (201/401/404/422) protegidos con `current_user`, el validador Pydantic v2 de `SongCreate`, la capa `services/songs.py` con excepción propia (`RelatedNotFound`), la diferencia entre `flush` y `commit`, y la corrección de `list_songs` (lista vacía = `200 []`). La suite cerró en **92 passed, 1 skipped** (más tarde 115 con las siguientes lecciones).
- Método: **el tutor escribe los tests (y los valida con una implementación de referencia y mutaciones), el usuario escribe el código y los commits.** Se resolvió con rojo → verde por pasos y filtros `-k`.
- Hubo muchos errores de tecleo (`artist_is`, `song_ids`, `fastappi`, `Depdends`); de ahí salieron dos comprobaciones de un segundo: `uvx ruff check --select F,E9 app tests` y `uv run python -c "import app.main"`.

## 2A. Paso a paso — catálogo de lectura y sobre de errores

> **Parte A de la lección 5.** Cubre todo lo que es *lectura* (`GET`) del catálogo y el formato de error unificado. La Parte B (escrituras protegidas `POST /artists` y `POST /songs`, y la capa de servicio) viene después de [[lesson-4]] (autenticación), porque necesita `current_user`.
>
> Marca `📝` = dato reconstruido o añadido al redactar estas notas (no es una cita literal del diálogo).
> Cronología real: del 22 oct (21:23) al 23 oct (04:02), con pausas. En el diálogo esta lección se llamaba "lección 5" (en el plan es el paso 5 de 7).

### 2A.0 Por qué el catálogo va antes que la autenticación

El usuario propuso hacer autenticación primero ("creo que es autenticación"). La recomendación, que aceptó ("estoy de acuerdo por ahora con este orden"), fue **canciones y artistas primero** por tres razones:

1. **Nada bloquea los endpoints de catálogo.** Son lecturas públicas. La autenticación la necesitan las playlists (dueño) y `/me`, no estos.
2. **Construye el patrón que la autenticación reutiliza:** `Depends(get_db)` → repositorio → modelo → schema. `current_user` es otro `Depends` que usa la misma sesión. Mejor aprenderlo con `GET` simples y añadir la seguridad después.
3. **Es el SQL que se pide en entrevista:** joins entre canciones, artistas y rol, y conteos por artista. Además se ve funcionando en `/docs`.

Con esto se "rellena la caja punteada del mapa": hasta entonces las rutas respondían 501 y `services/` y `repositories/` estaban vacíos (el mapa de capas se explicó en [[lesson-3]]).

Qué se construía en esta lección (resumen que dio el tutor):

- Conectar la sesión a los routers con `Depends(get_db)`.
- Escribir las consultas en `repositories/`: filtrar canciones por género, artista y texto, y listar las canciones de un artista con su rol.
- Armar `SongsOut.artists` y `ArtistsOut.genres`, que son **campos calculados**.
- Devolver 404 con el formato de error unificado cuando no exista el recurso.
- Reparto de trabajo: **el tutor escribe los tests, el usuario escribe el código**, igual que en la lección de modelos.

Plan ajustado en ese momento (la lección de modelos había tomado más de lo previsto):

| Día | Qué |
|---|---|
| 3 (23 oct) | Lección 5 (canciones y artistas) y autenticación |
| 4 (24 oct) | Playlists y React (`SongList`, `LoginForm`) |
| 5 (25 oct) | Simulacro de 90 min, diseño de streaming y narrativa de experiencia |

Orden de recortes si se aprieta: **Dockerfile → pandas/NumPy → playlists**.

`POST /artists` y `POST /songs` se dejaron para después de autenticar, porque exigen login (ver Parte B).

### 2A.1 Material que preparó el tutor antes de que el usuario escribiera una línea

Nada de esto toca el código de la app; son tests, una hoja de SQL y fixtures. Se validó todo contra una **solución de referencia que vivía solo en una copia temporal** (nunca en el repo del usuario).

#### a) Fixtures nuevas en `tests/conftest.py`

Se mantuvo la fixture `session` (SQLite en memoria) y se añadieron dos:

```python
@pytest.fixture
def db_factory(tmp_path):
    """Base SQLite en un archivo temporal, con las tablas creadas.

    Devuelve una fábrica de sesiones. Se usa un archivo (no ':memory:') porque
    TestClient ejecuta los endpoints en otro hilo y cada conexión a ':memory:'
    sería una base distinta y vacía.
    """
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401
    from app.db import Base, make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def client(db_factory):
    """TestClient cuya app usa la base temporal en lugar de data/music.db."""
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def override_get_db():
        with db_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Qué hace cada pieza (y por qué es una buena respuesta de entrevista):

- **`db_factory`** crea una base real **en un archivo** dentro de `tmp_path` (carpeta temporal que pytest crea y borra por test). No se usa `:memory:` porque `TestClient` ejecuta los endpoints en **otro hilo** y cada conexión a `:memory:` sería una base distinta y vacía.
- **`expire_on_commit=False`**: tras un `commit`, los objetos siguen utilizables sin releer de la base (misma opción que `SessionLocal` en `app/db.py`).
- **`client`** reemplaza la dependencia `get_db` por una sesión de la base temporal con `app.dependency_overrides`. **Esa es la ventaja de la inyección de dependencias:** el mismo código del router corre contra la base real en producción y contra una base temporal en tests, sin tocar el router.
- **`app.dependency_overrides.clear()`** al final, para que un test no contamine al siguiente.

#### b) `tests/test_catalog_api.py` (19 tests al inicio; 20 al final)

Se escribieron **contra una base real sembrada**, con un catálogo mínimo de prueba (`CATALOG`) cuyos ids se conocen de antemano:

```
géneros    Rock=1, Pop=2
artistas   Ana=1, Beto=2
canciones  Uno=1 (Rock, Ana main + Beto featured), Dos=2 (Pop, Ana), Tres=3 (Rock, Beto)
```

```python
CATALOG = {
    "artists": [
        {"name": "Ana", "songs": [
            {"title": "Uno", "duration_s": 200, "genre": "Rock", "featuring": ["Beto"]},
            {"title": "Dos", "duration_s": 180, "genre": "Pop"},
        ]},
        {"name": "Beto", "songs": [{"title": "Tres", "duration_s": 240, "genre": "Rock"}]},
    ]
}

@pytest.fixture
def seeded(db_factory):
    with db_factory() as s:
        assert seed_database(s, CATALOG) is True
```

El catálogo se siembra con la misma función `seed_database` de [[lesson-3]] (el script final que se le dio al usuario sobre su `flatten_catalog`): así los tests del catálogo también ejercitan la semilla.

Helpers: `titles(response)` y `names(response)` (comprueban `200` y devuelven la lista de títulos/nombres) y `add_playlist_with(db_factory, song_ids)` (crea un usuario y UNA playlist que contiene las canciones dadas; lo usa el test de stats).

Los tests están agrupados por pasos de la lección:

| Paso | Tests | Qué comprueban |
|---|---|---|
| 1 | `test_list_genres` | Orden `["Rock","Pop"]` y claves `{id, name, created_at}` |
| 2 | `test_get_song_with_genre_and_artists`, `test_get_song_not_found` | Género anidado y artistas con rol y orden; 404 |
| 3 | `test_list_songs_default_order`, `..._filter_by_genre`, `..._filter_by_artist_includes_featured`, `test_filter_by_artist_keeps_all_artists_of_each_song`, `..._search_by_title`, `..._combined_filters`, `..._pagination` | Orden por id, cada filtro, filtros combinados, `q` sin distinguir mayúsculas, `limit/offset` |
| 4 | `test_get_artist_with_genres`, `test_get_artist_not_found`, `test_list_artists`, `test_list_artists_is_sorted_by_name` (añadido después), `test_artist_songs`, `test_artist_stats_without_playlists`, `test_artist_stats_counts_each_playlist_once`, `test_artist_stats_not_found` | Géneros distintos y ordenados; 404; lista; orden por nombre; canciones de un artista; stats |
| 5 | `test_404_uses_error_envelope`, `test_validation_error_uses_error_envelope` | Formato `{"error": {"code", "message"}}` |

Cómo correrlos por pasos (cabecera del archivo):

```bash
uv run pytest tests/test_catalog_api.py -k test_list_genres -q
uv run pytest tests/test_catalog_api.py -k "get_song or list_songs" -q
uv run pytest tests/test_catalog_api.py -k "artist" -q
uv run pytest tests/test_catalog_api.py -k envelope -q
```

> ⚠️ Corrección del tutor: la primera versión sugería `-k genres`, pero ese patrón **también selecciona** `test_get_artist_with_genres` (del paso 4). Para el paso 1 hay que usar `-k test_list_genres`. (📝 la docstring del archivo todavía conserva el `-k genres` original.)

Detalle clave de diseño: algunos tests comprueban **cosas que se rompen en silencio**. Por ejemplo `test_filter_by_artist_keeps_all_artists_of_each_song` pide los artistas de `artist_id=2` (Beto) y exige que "Uno" siga mostrando **sus dos artistas** (Ana y Beto), no solo el filtrado. Eso detecta el error de filtrar con `JOIN` en lugar de `IN (subconsulta)` (ver 3A.8).

#### c) `sql/queries.sql` — la hoja de SQL

Cinco consultas que se prueban a mano sobre la base sembrada **antes** de escribirlas en Python (el SQL es lo que luego se traduce a `select(...)`):

```sql
-- Q1. Géneros (GET /genres)
SELECT id, name, created_at
FROM genres
ORDER BY id;

-- Q2. Canciones con filtros opcionales y paginación (GET /songs)
--     Filtro por artista con IN (subconsulta), no con JOIN: así cada canción
--     sale una sola vez y no se pierden sus otros artistas.
SELECT s.id, s.title, s.duration_s, s.genre_id
FROM songs s
WHERE s.genre_id = 1                                                  -- ?genre_id=
  AND s.id IN (SELECT song_id FROM song_artists WHERE artist_id = 1)  -- ?artist_id=
  AND LOWER(s.title) LIKE '%' || LOWER('a') || '%'                    -- ?q=
ORDER BY s.id
LIMIT 20 OFFSET 0;                                                    -- ?limit= &offset=

-- Q3. Artistas (con rol) de un grupo de canciones: UNA consulta para todas
--     las canciones de la página, en vez de una por canción (evita el N+1).
SELECT sa.song_id, a.id AS artist_id, a.name, sa.role
FROM song_artists sa
JOIN artists a ON a.id = sa.artist_id
WHERE sa.song_id IN (1, 2, 3)
ORDER BY sa.song_id, a.id;

-- Q4. Géneros distintos de un artista (ArtistsOut.genres, dato calculado)
SELECT DISTINCT g.name
FROM genres g
JOIN songs s         ON s.genre_id = g.id
JOIN song_artists sa ON sa.song_id = s.id
WHERE sa.artist_id = 1
ORDER BY g.name;

-- Q5. Estadísticas de un artista (GET /artists/{id}/stats)
--     song_count: la PK (song_id, artist_id) ya garantiza canciones distintas.
--     playlist_count: COUNT(DISTINCT ...) porque una playlist con 5 canciones
--     del artista cuenta una sola vez.
SELECT
  (SELECT COUNT(*) FROM song_artists WHERE artist_id = 1) AS song_count,
  (SELECT COUNT(DISTINCT ps.playlist_id)
     FROM playlist_songs ps
     JOIN song_artists sa ON sa.song_id = ps.song_id
    WHERE sa.artist_id = 1)                                AS playlist_count;
```

Se ejecutaron contra el `seed.json` real (13 artistas, 44 canciones, 8 géneros) y esto es lo que debe verse:

| Consulta | Resultado esperado con el seed real |
|---|---|
| Q1 | 8 géneros, con `created_at` lleno (Pop, Electrónica, Rock, Folk, Reggae, Jazz, Hip hop, Salsa) |
| Q2 | 2 canciones: `Bailar sin Mapa` (id 2) y `Todo Cambia` (id 4) |
| Q3 | Pares canción-artista con rol, p. ej. `(3, 1, 'Aurora Vega', 'main')` y `(3, 2, 'Cobalto', 'featured')` |
| Q4 | 3 géneros: Electrónica, Pop, Rock |
| Q5 | `song_count = 6`, `playlist_count = 0` |

Cómo correrla (en macOS el CLI `sqlite3` viene instalado):

```bash
uv run python -m app.seed
sqlite3 -header -column data/music.db < sql/queries.sql
```

Un primer intento de ejecutarla desde Python falló con `sqlite3.Warning: You can only execute one statement at a time` (el módulo `sqlite3` de Python ejecuta una sentencia por llamada) y Q2 devolvió 0 filas porque los ids de ejemplo no coincidían con el seed real; se ajustaron los valores de ejemplo (artista 1) y se añadió el comentario "en Q2 cada condición es opcional: bórrala para ver el efecto del filtro".

#### d) Cambio en `tests/test_contract.py`

`test_stubs_answer_501` comprobaba que `/genres` y `/songs` respondían 501. Al implementarlos dejarían de hacerlo, así que se cambió a:

```python
def test_stubs_answer_501():
    # Pendientes de las lecciones de auth y playlists. Borrar este test al terminarlas.
    assert client.get("/playlists").status_code == 501
    assert client.get("/me").status_code == 501
```

(Este test se eliminó/ajustó en las lecciones de auth y playlists. Ver [[lesson-4]] y [[lesson-6]].)

#### e) Cómo se validó el material (método del tutor)

1. Copia del repo a un directorio temporal (excluyendo `.venv`, `__pycache__`, `.pytest_cache`, `*.db`), `uv sync -q`.
2. **Sin solución:** `19 failed` (los tests dependen de la API, que aún responde 501). En el repo del usuario al empezar: `19 failed, 26 passed, 1 skipped` (la suite total).
3. **Con la solución de referencia** (repos, routers y handlers de error): `19 passed` en `test_catalog_api.py` y `45 passed, 1 skipped` en toda la suite.
4. **Mutaciones** (romper la solución de referencia a propósito y comprobar que algún test falla; si ninguno falla, el test es débil):

| Mutación | Test que la detecta |
|---|---|
| `playlist_count` sin `DISTINCT` | `test_artist_stats_counts_each_playlist_once` |
| géneros del artista sin `DISTINCT` | `test_get_artist_with_genres` |
| `offset` ignorado en canciones | `test_list_songs_pagination` |
| sin filtro por artista | `..._filter_by_artist_includes_featured`, `..._combined_filters`, `test_artist_songs` |
| `q` como igualdad exacta en vez de "contiene" | `test_list_songs_search_by_title` |

5. Comprobaciones extra:
   - **¿Hace falta `from_attributes` en los schemas?** Se probó quitándolo de `GenreOut`: **19 passed igualmente**. FastAPI valida objetos ORM contra el `response_model` por su cuenta (ver 3A.14). *Corrección del tutor:* antes había dicho que los schemas lo necesitaban.
   - **Sin `Genre.created_at`** el endpoint falla con `fastapi.exceptions.ResponseValidationError: 2 validation errors ... 'loc': ('response', 0, 'created_at'), 'msg': 'Field required'` → es lo que motivó el Paso 0.

#### f) La ruta de la lección que se le entregó al usuario

| Paso | Qué | Test (`uv run pytest tests/test_catalog_api.py -k ... -q`) |
|---|---|---|
| 0 | `Genre.created_at` | — |
| 1 | `GET /genres` | `test_list_genres` |
| 2 | `GET /songs/{id}` con género y artistas | `get_song` |
| 3 | `GET /songs` con filtros y paginación | `list_songs or filter_by` |
| 4 | Los 4 endpoints de artistas, con `stats` | `artist` |
| 5 | Formato de error unificado | `envelope` |

> En la práctica el usuario hizo el orden 0 → 1 → 2 → 4a (artista) → 4b → 4c → **3 (lista de canciones)** → `/artists/{id}/songs` → 5, porque `GET /artists/{id}/songs` reutiliza la consulta del paso 3.

---

### 2A.2 Paso 0 — la columna `created_at` que faltaba en `genres`

**El problema.** `GenreOut` (en `schemas.py`) exige `created_at`, pero la tabla `genres` no tenía esa columna. La primera llamada a `/genres` habría fallado con `ResponseValidationError: created_at Field required`. Es un **desajuste entre schema y modelo**.

**Estado antes** (`app/models.py`):

```python
class Genre(Base):
    __tablename__ = "genres"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
```

**Cambio** (0.1): añadir debajo de `name` la misma línea que ya tenían `User`, `Artist` y `Song`:

```python
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

`server_default` significa que **la base de datos pone la fecha al insertar**. Por eso `seed.py` no cambia: sus filas no traen `created_at` y la base lo rellena sola.

**0.2 Comprobar que no se rompió nada:**

```bash
uv run pytest tests/test_models.py -q      # debe seguir dando: 14 passed
```

**0.3 Recrear la base.** `create_all` **no modifica tablas que ya existen**: el `music.db` que ya había se creó sin la columna. Se borra y se vuelve a sembrar:

```bash
rm data/music.db
uv run python -m app.seed                  # debe imprimir: sembrada
sqlite3 data/music.db ".schema genres"     # debe aparecer: created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
```

DDL esperado de la tabla:

```sql
CREATE TABLE genres (
    id INTEGER NOT NULL,
    name VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (id),
    UNIQUE (name)
)
```

Esto es lo que en proyectos reales resuelven las **migraciones (Alembic)**: cambiar una tabla existente sin perder datos. Aquí basta con recrear la base, y en la entrevista se puede decir exactamente así.

**0.4 Mirar los datos con las consultas** (`sqlite3 -header -column data/music.db < sql/queries.sql`, tabla de resultados esperados arriba) y hacer un experimento: **borrar la línea del filtro por artista en Q2** y volver a correrla. Aparecen más canciones, y así se ve qué hace cada condición.

**Si algo falla:**

| Síntoma | Causa |
|---|---|
| `no such column: created_at` | No se recreó la base. Repetir 0.3 |
| `no such table` | `music.db` quedó vacío. `uv run python -m app.seed` |
| Sale `ya estaba sembrada` en vez de `sembrada` | El `rm` no borró el archivo. Revisar que se está en `backend/` |

**Resultado del usuario:** el modelo `Genre` ya tenía `created_at` y el `music.db` era el nuevo (73 728 bytes). Paso 0 correcto.

---

### 2A.3 Paso 1 — `GET /genres` (primer endpoint conectado de punta a punta)

Flujo que se construye:

```
GET /genres  →  router (genres.py)  →  repositorio (repositories/genres.py)  →  Session  →  tabla genres
```

- El **repositorio** solo habla con la base de datos: recibe una sesión y devuelve objetos del modelo.
- El **router** recibe la request y delega en el repositorio; **nunca escribe SQL**.

**Se entregó con huecos (`...`)** para que el usuario los rellenara:

```python
# app/repositories/genres.py   (hay que crear también app/repositories/__init__.py, vacío)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def list_genres(db: Session) -> list[models.Genre]:
    stmt = select(models.Genre).order_by(...)
    return list(db.scalars(stmt))
```

```python
# app/routers/genres.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import genres as genres_repo
from app.schemas import GenreOut

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(db: Session = Depends(...)):
    return ...      # llama al repositorio pasándole db
```

**Versión final del usuario (verde):**

```python
# repositories/genres.py
def list_genres(db: Session) -> list[models.Genre]:
    stmt = select(models.Genre).order_by(models.Genre.id)
    return list(db.scalars(stmt))
```

```python
# routers/genres.py
@router.get("", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)):
    return genres_repo.list_genres(db)
```

**Explicaciones dadas:**

- `select(models.Genre).order_by(...)` es la Q1 de `queries.sql` escrita en Python. **Solo describe** la consulta; todavía no la ejecuta.
- `db.scalars(stmt)` la **ejecuta** y devuelve objetos `Genre`; `list(...)` los junta.
- `Depends(get_db)`: al llegar la request, FastAPI llama a `get_db`, pasa la sesión como `db` y la **cierra cuando la respuesta sale**. El router no abre ni cierra nada.
- `return`: FastAPI convierte lo devuelto a `GenreOut` y a JSON.
- `HTTPException` desaparece de los imports del router de géneros porque ya no se lanza el 501.

**Cómo se probó:**

```bash
uv run pytest tests/test_catalog_api.py -k test_list_genres -q      # 1 passed
uv run uvicorn app.main:app --reload                                  # y abrir http://127.0.0.1:8000/docs
```

En `/docs`: desplegar `GET /genres` → **Try it out** → **Execute**. Salen los 8 géneros con su `created_at`, leídos de `data/music.db`. El test usa una base temporal; el servidor usa el archivo real. **Esa diferencia sale de `Depends(get_db)`** y es lo que hace testeable el diseño.

Salida real comprobada con `curl` contra el servidor sembrado:

```json
[{"id":1,"name":"Pop","created_at":"2026-10-22T21:27:15"},{"id":2,"name":"Electrónica","created_at":"2026-10-22T21:27:15"}, ...]
```

**Errores típicos de este paso (el tutor los provocó a propósito para documentarlos):**

| Síntoma | Causa |
|---|---|
| `FastAPIError: Invalid args for response field! ... Session` al arrancar | Se escribió `db: Session` sin `= Depends(get_db)`. FastAPI cree que `Session` es un campo de la respuesta |
| `ResponseValidationError: Input should be a valid list, input: None` | Falta el `return` en el router (la función devuelve `None`) |
| `assert 501 == 200` | Sigue el código viejo del router |
| `ImportError` de `app.repositories` | Nombre de carpeta mal o `genres.py` fuera de la carpeta |

---

### 2A.4 Paso 2 — `GET /songs/{song_id}` (una canción con género y artistas)

**Qué tiene que devolver.** `SongsOut` mezcla **tres fuentes**; una tabla sola no basta:

| Campo | De dónde sale |
|---|---|
| `id`, `title`, `duration_s`, `created_at` | tabla `songs` |
| `genre` (id, name, created_at) | tabla `genres`, por `songs.genre_id` |
| `artists` (artist_id, name, role) | `song_artists` unida a `artists` (la Q3 con un solo id) |

Por eso el repositorio arma el resultado con **tres consultas pequeñas**.

**Esqueleto entregado** (cuatro huecos):

```python
def get_song(db: Session, song_id: int) -> dict | None:
    song = db.get(models.Song, song_id)          # busca por clave primaria
    if song is None:
        return None
    genre = db.get(models.Genre, song.genre_id)
    rows = db.execute(
        select(models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, ...)                # el ON del JOIN de Q3
        .where(...)                              # solo los artistas de ESTA canción
        .order_by(...)                           # por artist_id
    ).all()
    return {
        "id": song.id,
        "title": ...,
        "duration_s": ...,
        "created_at": ...,
        "genre": genre,
        "artists": [{"artist_id": r.artist_id, "name": r.name, "role": r.role} for r in rows],
    }
```

```python
# router: solo cambia get_song; los demás endpoints siguen siendo stubs
@router.get("/{song_id}", response_model=SongsOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = ...                                    # llama al repositorio
    if song is None:
        raise HTTPException(status_code=..., detail=f"Song {song_id} not found")
    return song
```

Ideas clave:

- `db.get(Modelo, id)` es el `SELECT ... WHERE id = ?` por clave primaria; devuelve el objeto o `None`.
- El `.join(models.Artist, <condición>)` es el `JOIN artists a ON a.id = sa.artist_id` de Q3.
- Las **claves del diccionario** deben llamarse igual que los campos de `SongsOut` / `SongsArtistOut` (`artist_id`, `name`, `role`): FastAPI valida el dict contra el schema.
- `genre` es un objeto `Genre` completo; FastAPI lo convierte a `GenreOut` solo.
- **El 404 lo decide el router, no el repositorio**: 404 es un concepto HTTP. El repositorio solo dice `None` cuando no encuentra nada.

**Pruebas:**

```bash
uv run pytest tests/test_catalog_api.py -k get_song -q    # 2 passed
```

Y en vivo en `/docs`: `GET /songs/3` (devuelve el género y dos artistas, uno `main` y otro `featured` con el seed) y `GET /songs/999` → 404 con `{"detail": "Song 999 not found"}` (el formato definitivo del error llega en el Paso 5).

Error provocado para documentar: olvidar el chequeo de `None` produce `AttributeError: 'NoneType' object has no attribute 'genre_id'`.

#### La propuesta del usuario y la revisión

Primera versión que escribió el usuario:

```python
from sqlalchemi import select                       # ← (1) typo
from sqlalchemy.orm import Session

from app import models

def get_song(db:Session, song_id: int) -> dict | None:
    song = db.get(models.Song, song_id)
    if song is None:
        return None

    genre = db.get(models.Song, song_id)            # ← (2) pide la canción otra vez, no el género
    rows = db.execute(
        select(models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, models.SongArtist.artist_id == models.Artist.id)
        .where(models.SongArtist == song_id)        # ← (3) compara la CLASE con un número
        .order_by(models.SongArtist.artist_id)
    ).all()

    return {
        "id": song_id,
        "title": rows.title,                        # ← (4) rows es la lista de artistas, no la canción
        "duration_s": rows.duration_s,
        "created_at": rows.created_at,
        "genre": rows.genre,
        "artists": [{"artist_id": r.artist_id,"name":r.name, "role":r.role} for r in rows]
    }
```

Lo que estaba **bien**: `db.get(models.Song, song_id)` con el chequeo de `None`, las tres columnas del `select`, el `join` con su condición, el `order_by` y la lista de artistas con `r.artist_id`, `r.name`, `r.role`. Veredicto del tutor: "tu estructura está bien".

Los cuatro errores:

| Línea | Problema | Por qué |
|---|---|---|
| 1 | `sqlalchemi` | Falta la `y`. `ModuleNotFoundError: No module named 'sqlalchemi'` |
| 11 | `genre = db.get(models.Song, song_id)` | Vuelve a pedir la canción, no el género. El género está en la tabla `genres` y su id es `song.genre_id` |
| 15 | `.where(models.SongArtist == song_id)` | Se compara la clase entera con un número. En Python eso da `False` y SQLAlchemy lo convierte en `WHERE false`: **no da error** y los artistas salen vacíos |
| 21–24 | `rows.title`, `rows.duration_s`, `rows.created_at`, `rows.genre` | `rows` es la lista de artistas del join. Esos campos pertenecen a `song` y a `genre` |

Detalle menor opcional: usar `song.id` en vez de `song_id` para que todos los campos salgan de `song`.

**En qué orden aparecían los errores** (el tutor lo reprodujo en una copia, arreglando uno a uno):

1. `ModuleNotFoundError` por el import.
2. `AttributeError: 'list' object has no attribute 'title'`, por el diccionario.
3. El tercero es **silencioso**: sin excepción, pero `artists == []` y el test falla (`AssertionError: assert [] == [{'artist_id'...: 'featured'}]`). Solo se ve porque el test compara el resultado.

**Regla para recordarlo.** Esta función tiene tres fuentes de datos y cada variable es una de ellas:

- `song` → título, duración y fecha.
- `genre` → el género.
- `rows` → los artistas.

*"Todo el error del diccionario era mezclar las fuentes. Antes de escribir cada campo, pregúntate de cuál viene."*

El usuario pidió ver la solución ("en este caso muéstrame la solución") y se le dio la versión corregida del repositorio **más el paso 2.2 que faltaba** (su `routers/songs.py` aún tenía el stub con el 501, así que aunque arreglara el repositorio el test seguiría dando `assert 501 == 200`):

```python
# app/repositories/songs.py
def get_song(db: Session, song_id: int) -> dict | None:
    song = db.get(models.Song, song_id)
    if song is None:
        return None

    genre = db.get(models.Genre, song.genre_id)
    rows = db.execute(
        select(models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, models.SongArtist.artist_id == models.Artist.id)
        .where(models.SongArtist.song_id == song_id)
        .order_by(models.SongArtist.artist_id)
    ).all()

    return {
        "id": song.id,
        "title": song.title,
        "duration_s": song.duration_s,
        "created_at": song.created_at,
        "genre": genre,
        "artists": [{"artist_id": r.artist_id, "name": r.name, "role": r.role} for r in rows],
    }
```

```python
# app/routers/songs.py  (imports nuevos + función)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import songs as songs_repo

@router.get("/{song_id}", response_model=SongsOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = songs_repo.get_song(db, song_id)
    if song is None:
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")
    return song
```

**La vuelta del error silencioso.** Horas después (23 oct, 01:02) el usuario volvió con exactamente ese fallo:

```
>       assert song["artists"] == [ {"artist_id": 1, "name": "Ana", "role": "main"}, ... ]
E       AssertionError: assert [] == [{'artist_id'...: 'featured'}]
```

El tutor leyó el archivo y encontró que **solo quedaba sin arreglar la línea 15**: `.where(models.SongArtist == song_id)`. Todo lo demás (género, diccionario, router, imports) ya estaba corregido, por eso el test avanzaba hasta comparar `artists`. Explicación:

`models.SongArtist` es la **clase entera**, no una columna. `models.SongArtist == song_id` compara una clase con un número, en Python da `False`, y SQLAlchemy lo convierte en:

```sql
SELECT ... FROM song_artists JOIN artists ... WHERE false
```

La consulta se ejecuta bien y no devuelve filas. `rows` queda vacío, mientras que título, duración y género sí llegan porque salen de otras consultas.

**Cómo detectar este tipo de error en el futuro:**

- Si un `select` devuelve `[]` sin error, **mirar primero el `where`**.
- `print(stmt)`: si aparece `WHERE false`, la comparación está mal escrita.
- Si un lado del `==` empieza con mayúscula y no tiene punto + columna detrás (`models.SongArtist` en vez de `models.SongArtist.song_id`), es una clase, no una columna.

El usuario lo corrigió: "listo esto esta corregido, sigamos con artists".

---

### 2A.5 Paso 4 — Artistas (4a `GET /artists/{id}`, 4b `GET /artists`, 4c `GET /artists/{id}/stats`)

#### 4a. `get_artist` y los géneros calculados

Primero hubo que **desbloquear toda la suite**. Al empezar con artistas, el usuario tenía dos errores en `routers/artists.py` que rompían la *recolección* de tests (`2 errors during collection`, ningún test llegaba a correr, ni siquiera `test_health.py`):

| Línea | Tenía | Debe ser |
|---|---|---|
| 2 | `from sqlalchemy import Session` | `from sqlalchemy.orm import Session` (`ImportError: cannot import name 'Session' from 'sqlalchemy'`) |
| 40 | `Depdends(get_db)` | `Depends(get_db)` (`NameError: name 'Depdends' is not defined`) |

Con esos dos cambios (probados en una copia) pasaron los 28 tests de lo ya implementado (`28 passed, 1 skipped`). Su `get_artist` del router ya estaba bien conectado: llama al repositorio, convierte `None` en 404 y devuelve el resultado, igual que `get_song`.

Repositorio: el usuario se había quedado justo después del `return None`. Faltaba calcular los **géneros del artista** (Q4 de `queries.sql`). Esqueleto con huecos:

```python
    genres = list(db.scalars(
        select(models.Genre.name).distinct()
        .join(models.Song, models.Song.genre_id == models.Genre.id)
        .join(models.SongArtist, ...)        # une canciones con sus artistas
        .where(...)                          # solo las canciones de ESTE artista
        .order_by(models.Genre.name)
    ))
    return {"id": ..., "name": ..., "created_at": ..., "genres": genres}
```

- El primer `.join` ya venía escrito para enseñar el patrón `.join(Tabla, condición)`.
- **`.distinct()` es obligatorio.** Beto tiene dos canciones de Rock; sin él saldría `['Rock', 'Rock']` (error documentado: `assert ['Rock', 'Rock'] == ['Rock']`).
- `genres` es un dato **calculado**, no una columna de `artists`: el diccionario junta lo de la tabla `artists` con lo que sale del `select`.
- Dos filtros que se olvidan fácil: `.where` con la columna `artist_id` de `SongArtist`, y `.order_by` por nombre (el test espera orden alfabético).
- El tutor adelantó el plan: 4b repetiría el cálculo de géneros para cada artista, así que entonces se extraería una función auxiliar — *"se refactoriza cuando el código se duplica, no antes"*.

Pruebas: `uv run pytest tests/test_catalog_api.py -k test_get_artist -q` → 2 passed (artista con géneros y el 404).

**Resultado del usuario** (versión final que está en el repo):

```python
def get_artist(db: Session, artist_id: int) -> dict | None:
    artist = db.get(models.Artist, artist_id)
    if artist is None:
        return None

    genres = list(db.scalars(
        select(models.Genre.name).distinct()
        .join(models.Song, models.Song.genre_id == models.Genre.id)
        .join(models.SongArtist, models.SongArtist.song_id == models.Song.id)
        .where(models.SongArtist.artist_id == artist_id)
        .order_by(models.Genre.name)
    ))
    return {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "created_at": artist.created_at,
    }
```

El tutor comprobó esto como correcto: "Tu 4a está bien".

#### Pregunta lateral: `db.execute` frente a `db.scalars` (y `db.scalar`)

Pregunta del usuario: *"¿cuál es la diferencia entre db.scalars y meter ahí el query como hicimos en songs, que en songs tenemos db.execute?"*

Respuesta: se diferencian **en lo que devuelven**; la regla es cuántas columnas pides.

| | Qué devuelve | Cuándo |
|---|---|---|
| `db.execute(stmt)` | Filas (`Row`), con todas las columnas del `select` | Pides **varias columnas** |
| `db.scalars(stmt)` | Solo la **primera columna** de cada fila, sin envoltorio | Pides **una sola cosa** |
| `db.scalar(stmt)` | Un único valor: la primera columna de la primera fila | Un conteo o un `max` |

En su código:

```python
# songs: tres columnas → execute, y cada fila se lee por nombre
rows = db.execute(select(SongArtist.artist_id, Artist.name, SongArtist.role)...).all()
# [(1, 'Ana', 'main'), (2, 'Beto', 'featured')]  →  r.artist_id, r.name, r.role

# géneros de un artista: una columna → scalars
db.scalars(select(Genre.name)...)        # ['Pop', 'Rock'] → ya es una lista de textos

# genres: una entidad completa → scalars
db.scalars(select(Genre))                # [<Genre 1>, <Genre 2>, ...] → objetos del modelo

# stats: un número → scalar (singular)
db.scalar(select(func.count())...)       # 6
```

`db.scalars(x)` es un atajo de `db.execute(x).scalars()`.

Errores típicos:

- **`scalars` con varias columnas:** SQLAlchemy se queda con la primera y descarta el resto **sin avisar**. En `songs` habría dado `[1, 2]` en vez de filas y `r.name` fallaría con `'int' object has no attribute 'name'`.
- **`execute` con una entidad:** `db.execute(select(Genre))` devuelve filas de un elemento `(Genre,)`, no objetos `Genre`; habría que escribir `.scalars()` o `row[0]`.

Atajo: mira qué hay dentro del `select(...)` — una sola columna o una sola clase → `scalars`; varias columnas → `execute`.

#### 4b. `GET /artists` (lista), `_genres_of`/`_to_out` y la reutilización de `get_artist`

Qué se pidió: la lista de artistas con `q`, `limit` y `offset`, y cada artista con sus géneros.

Primera propuesta del tutor (dos funciones auxiliares):

```python
def _genres_of(db: Session, artist_id: int) -> list[str]:
    stmt = (
        select(models.Genre.name).distinct()
        .join(models.Song, models.Song.genre_id == models.Genre.id)
        .join(models.SongArtist, models.SongArtist.song_id == models.Song.id)
        .where(models.SongArtist.artist_id == artist_id)
        .order_by(models.Genre.name)
    )
    return list(db.scalars(stmt))


def _to_out(db: Session, artist: models.Artist) -> dict:
    return {"id": artist.id, "name": artist.name, "created_at": artist.created_at,
            "genres": _genres_of(db, artist.id)}
```

```python
def list_artists(db: Session, q: str | None, limit: int, offset: int) -> list[dict]:
    stmt = select(models.Artist)
    if q:
        stmt = stmt.where(models.Artist.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(...).limit(...).offset(...)
    return [_to_out(db, a) for a in db.scalars(stmt)]
```

- `stmt = stmt.where(...)`: **hay que reasignar**, porque cada método devuelve una consulta nueva y no modifica la anterior (los statements son inmutables).
- `ilike(f"%{q}%")` busca el texto en cualquier parte del nombre, sin distinguir mayúsculas.
- Router: añadir como **último parámetro** `db: Session = Depends(get_db)` y sustituir el `raise` por `return artists_repo.list_artists(db, q, limit, offset)`.
- Test: `-k test_list_artists`.
- Aviso de N+1: esta versión lanza **una consulta de géneros por artista**. Con límite 20 es aceptable; en la entrevista se puede decir que se resolvería con una sola consulta con `IN`, "como haremos con las canciones".

**Pregunta lateral del usuario:** *"un poco perdido en cuanto a qué es esa función `_genres_of` y `_to_out`. Y me pregunto si en el repositorio la función `get_artist` puede ser reutilizada por `list_artists` para no reescribir el código."*

Respuesta:

- **`_genres_of(db, artist_id)`**: el bloque de géneros que ya escribió el usuario en `get_artist` (su Q4), metido en su propia función. Recibe un artista y devuelve sus géneros, p. ej. `['Pop', 'Rock']`.
- **`_to_out(db, artist)`**: convierte un objeto `Artist` (una fila) en el diccionario con la forma de `ArtistsOut`: `id`, `name`, `created_at` y `genres`. **"Out" = "de salida"**, lo que devuelve la API.
- **El guion bajo** es una convención de Python: "función interna de este archivo, que los routers no usan directamente".
- Las dos existían para que `get_artist` y `list_artists` compartieran el cálculo. **Pero si `list_artists` llama a `get_artist`, ese reparto ya no hace falta.**

Medición (13 artistas del seed, con un contador de consultas vía el evento `before_cursor_execute`):

| Enfoque | Resultado |
|---|---|
| `list_artists` llamando a `get_artist` por cada artista | 13 artistas → **14 consultas** |
| Helper `_to_out` | 13 artistas → **14 consultas** |

Ambos: 1 para la lista + 1 de géneros por artista. `db.get` **no repite la consulta** del artista porque la sesión ya lo tiene cargado (identity map; ver 3A.4).

Conclusión: sí, se puede reutilizar. Es más corto y los tests pasan (3 passed en `test_list_artists` + `test_get_artist`). Lo que se pierde es solo precisión de tipos: `get_artist` devuelve `dict | None` y en la lista nunca será `None`. "La versión con `_to_out` es un poco más limpia, pero con la que ya tienes avanzas más rápido." El usuario siguió la versión corta:

```python
def list_artists(db: Session, q: str | None, limit: int, offset: int) -> list[dict]:
    stmt = select(models.Artist)
    if q:
        stmt = stmt.where(models.Artist.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(models.Artist.id).limit(limit).offset(offset)
    return [get_artist(db, a.id) for a in db.scalars(stmt)]
```

**Requisito nuevo: ordenar por nombre.** El usuario avisó: *"el requerimiento es ordenar los artistas por nombre, porque yo los estoy organizando por ID."* El cambio es de una palabra: `order_by(models.Artist.id)` → `order_by(models.Artist.name)`.

Por qué el tutor **añadió un test nuevo**: con el catálogo de prueba (Ana id 1, Beto id 2) el orden por id y por nombre coinciden, así que `test_list_artists` pasaba con ambos y no detectaba la diferencia. Se añadió `test_list_artists_is_sorted_by_name`, que crea tres artistas cuyos ids van **al revés del alfabeto** (Zoe=1, Abel=2, Marta=3) y exige `["Abel", "Marta", "Zoe"]`, incluida la paginación:

```python
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
```

Comprobado en copia: con `order_by(Artist.id)` falla (`['Zoe', 'Abel', 'Marta']`), con `name` pasa. Además se anotó en el README, junto a la paginación: *"`GET /artists` ordena por nombre; las demás listas, por id."*

Dos detalles del orden por nombre:

- **La paginación sigue siendo estable.** `Artist.name` es único (`unique=True` en el modelo), así que dos artistas nunca empatan y `limit`/`offset` no repiten ni saltan filas. Si se ordenara por una columna que se repite, haría falta un segundo criterio: `.order_by(Artist.name, Artist.id)`.
- **El orden distingue mayúsculas de minúsculas en SQLite:** una "marta" en minúscula saldría después de "Zoe". En el `seed.json` todos los nombres empiezan con mayúscula ASCII (13 nombres comprobados), así que no afecta hoy. Si importara: `func.lower(models.Artist.name)`.

Resultado: "todo en verde, sigamos". Estado de la suite tras 4b: `13 failed, 33 passed, 1 skipped`.

#### 4c. `GET /artists/{id}/stats` (dos conteos, el segundo con `COUNT(DISTINCT)`)

Esqueleto entregado (imports: `from sqlalchemy import distinct, func, select`):

```python
def get_stats(db: Session, artist_id: int) -> dict | None:
    if db.get(models.Artist, artist_id) is None:
        return None
    song_count = db.scalar(
        select(func.count()).select_from(models.SongArtist).where(...)
    )
    playlist_count = db.scalar(
        select(func.count(distinct(...)))
        .select_from(models.PlaylistSong)
        .join(models.SongArtist, ...)
        .where(...)
    )
    return {"artist_id": artist_id, "song_count": song_count, "playlist_count": playlist_count}
```

- **`song_count`**: cuántas filas de `song_artists` tiene ese artista. La clave primaria compuesta `(song_id, artist_id)` garantiza que no se repiten canciones → no hace falta `DISTINCT`.
- **`playlist_count`**: cuántas playlists **distintas** contienen alguna canción suya. Cuenta `playlist_id` con `DISTINCT`, porque una playlist con cinco canciones del mismo artista cuenta **una sola vez**. La condición del `join` une `playlist_songs` con `song_artists` por la canción.
- **`db.scalar`** (singular): cada consulta devuelve un solo número.
- Es la Q5 de `queries.sql`.
- En el router, `get_artist_stats` copia el patrón de `get_artist`: llama a `artists_repo.get_stats`, lanza 404 si es `None` y devuelve el resultado. El usuario ya lo tenía así; fallaba con `AttributeError` solo porque `get_stats` no existía todavía.
- Test: `-k stats` (3 tests: sin playlists, el conteo sin repetir y el 404).

**Primer intento del usuario y su error.** Salida que pegó:

```
.F.
test_artist_stats_counts_each_playlist_once
    add_playlist_with(db_factory, [1, 2])    # Uno y Dos (ambas de Ana) en la MISMA playlist
>   assert client.get("/artists/1/stats").json() == {"artist_id": 1, "song_count": 2, "playlist_count": 1}
E   {'playlist_count': 2} != {'playlist_count': 1}
```

Su código tenía `select(func.count())` sin `DISTINCT` en `playlist_count`. Qué pasa en el test: Uno y Dos (las dos canciones de Ana) están en la **misma** playlist. Al unir `playlist_songs` con `song_artists` salen **dos filas**:

| playlist_id | song_id | artist_id |
|---|---|---|
| 1 | 1 (Uno) | 1 (Ana) |
| 1 | 2 (Dos) | 1 (Ana) |

`COUNT(*)` cuenta 2, pero es una sola playlist. Lo que se quiere es "cuántas playlists distintas tienen alguna canción de Ana".

**Segundo intento** (pegó el archivo entero y preguntó "¿es esta la solución?"): puso `.distinct()` *después* de `.select_from(models.PlaylistSong)`:

```python
playlist_count = db.scalar(
    select(func.count())
    .select_from(models.PlaylistSong).distinct()      # ← sigue fallando
    .join(models.SongArtist, models.SongArtist.song_id == models.PlaylistSong.song_id)
    .where(models.SongArtist.artist_id == artist_id)
)
```

El tutor lo ejecutó tal cual: falla igual (`playlist_count: 2`). El SQL que genera:

```sql
SELECT DISTINCT count(*) AS count_1
FROM playlist_songs JOIN song_artists ON song_artists.song_id = playlist_songs.song_id
WHERE song_artists.artist_id = :artist_id_1
```

Ese `DISTINCT` se aplica al **resultado final**, que ya es una sola fila con un número (el 2); quitar duplicados de una sola fila no cambia nada. Primero se cuentan las filas del join y luego se aplica el `DISTINCT`. Lo que se necesita es el `DISTINCT` **dentro** del conteo:

```sql
SELECT count(DISTINCT playlist_songs.playlist_id) ...
```

**Solución (la del repo ahora):**

```python
def get_stats(db: Session, artist_id: int) -> dict | None:
    artist = db.get(models.Artist, artist_id)
    if artist is None:
        return None

    song_count = db.scalar(
        select(func.count())
        .select_from(models.SongArtist)
        .where(models.SongArtist.artist_id == artist_id)
    )

    playlist_count = db.scalar(
        select(func.count(distinct(models.PlaylistSong.playlist_id)))
        .select_from(models.PlaylistSong)
        .join(models.SongArtist, models.SongArtist.song_id == models.PlaylistSong.song_id)
        .where(models.SongArtist.artist_id == artist_id)
    )

    return {"artist_id": artist_id, "song_count": song_count, "playlist_count": playlist_count}
```

Dos usos distintos de "distinct" (tabla que dio el tutor para fijar la idea):

| Dónde | Qué hace |
|---|---|
| `select(...).distinct()` | Quita filas repetidas del **resultado**. Se usó bien en `get_artist` con los nombres de géneros |
| `func.count(distinct(col))` | Cuenta los **valores distintos** de una columna. Es lo necesario aquí |

En `get_artist` funcionaba porque hay una fila por género; en `get_stats` el resultado es un solo número, así que no hay nada que deduplicar.

**Regla:** cuando un `JOIN` multiplica filas (una playlist por cada canción suya), cuenta con `DISTINCT` la entidad que realmente quieres contar.

Detalle pendiente que se señaló: `get_stats` declaraba `-> dict` pero devuelve `None` si no existe el artista → debe ser `-> dict | None`. (En el repo actual ya está corregido.) Resultado: "listo, tenemos verde, que sigue?". Suite: `10 failed, 36 passed, 1 skipped`.

---

### 2A.6 Paso 3 — `GET /songs` con filtros y paginación (y el problema N+1)

**Por qué no basta con reutilizar `get_song`.** Si se hiciera `[get_song(db, s.id) for s in songs]`, cada canción dispararía sus propias consultas. El tutor lo midió en una copia temporal con 20 canciones (contando consultas con `event.listen(engine, "before_cursor_execute", ...)`):

| Enfoque | Consultas SQL |
|---|---|
| Un `get_song` por canción (ingenuo) | **25** |
| Lote con `IN` | **2** |

(Ambas cifras **no cuentan** la consulta que trae las 20 canciones de la página: la medición empezó después de cargarlas.)

Es el **problema N+1**. En entrevista suele salir como *"¿qué pasa si la página tiene 100 canciones?"*: el primer enfoque haría unas 125 consultas y el segundo seguiría en 2.

> 📝 Precisión: antes de medir, la explicación decía "tres consultas por canción"; la medición real fue 25 para 20 canciones. Cuadra porque `db.get` reutiliza lo ya cargado en la sesión (identity map): la canción ya está en la sesión (0 consultas) y el género solo se consulta la primera vez que aparece, así que el coste real queda en ≈ 20 de artistas + unos 5 géneros distintos (cifra de los géneros: inferida, no medida por separado). Lo importante es que crece **linealmente con N**, mientras que el lote se queda en 2.

**La idea, en tres partes:**

1. Una consulta trae las canciones de la página, con filtros, orden y paginación.
2. Una consulta trae los géneros de esas canciones: `Genre.id IN (...)`.
3. Una consulta trae los artistas de esas canciones: `SongArtist.song_id IN (...)`, y se agrupan por `song_id` en un diccionario.

**Esqueleto entregado:**

```python
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import models


def _to_out(db: Session, songs: list[models.Song]) -> list[dict]:
    if not songs:
        return []

    # consulta 2: géneros de TODAS las canciones de la página
    genre_ids = {s.genre_id for s in songs}
    genres = {g.id: g for g in db.scalars(select(models.Genre).where(models.Genre.id.in_(...)))}

    # consulta 3: artistas de TODAS las canciones, con su rol
    rows = db.execute(
        select(models.SongArtist.song_id, models.SongArtist.artist_id,
               models.Artist.name, models.SongArtist.role)
        .join(models.Artist, ...)
        .where(models.SongArtist.song_id.in_(...))
        .order_by(models.SongArtist.song_id, models.SongArtist.artist_id)
    ).all()

    by_song = defaultdict(list)
    for r in rows:
        by_song[r.song_id].append({"artist_id": ..., "name": ..., "role": ...})

    return [
        {"id": s.id, "title": s.title, "duration_s": s.duration_s,
         "created_at": s.created_at, "genre": genres[s.genre_id],
         "artists": by_song[s.id]}
        for s in songs
    ]


def list_songs(db: Session, genre_id=None, artist_id=None, q=None,
               limit: int = 20, offset: int = 0) -> list[dict]:
    stmt = select(models.Song)
    if genre_id is not None:
        stmt = stmt.where(...)
    if artist_id is not None:
        # IN (subconsulta), no JOIN: con JOIN la fila se duplicaría
        # y el filtro dejaría fuera a los demás artistas de la canción
        stmt = stmt.where(models.Song.id.in_(select(...).where(...)))
    if q:
        stmt = stmt.where(models.Song.title.ilike(...))
    stmt = stmt.order_by(...).limit(...).offset(...)
    return _to_out(db, list(db.scalars(stmt)))
```

Tres detalles que se subrayaron:

- **Reasignar el statement:** `stmt = stmt.where(...)`. Si no, el filtro se pierde en silencio.
- **El filtro por artista usa `IN (subquery)`, no `JOIN`.** Con JOIN, `artist_id=2` en "Uno" devolvería solo a Beto, y falla `test_filter_by_artist_keeps_all_artists_of_each_song`.
- **`if not songs: return []`** evita un `IN ()` vacío.

Router: mismo patrón que `get_song`; añadir `db: Session = Depends(get_db)` a `list_songs` y devolver `songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)`; quitar el `raise 501`. Los parámetros `limit`/`offset` del router llevan `Query(20, ge=1, le=100)` / `Query(0, ge=0)` (ya existían en el stub desde [[lesson-2]]).

```bash
uv run pytest tests/test_catalog_api.py -k "list_songs or filter_by_artist" -q      # 7 tests
```

**Primer intento del usuario: `7 failed`** ("algo salió mal en los tests, tenemos 7 failed, que es?"). El tutor corrió la suite sobre una copia. Versión del usuario de `repositories/songs.py` (extracto) y los 4 errores:

```python
def _to_out(db:Session, songs: list[models.Song]) -> list[dict]:
    ...
    genre_ids = [s.genre_id for s in songs]
    ...
        .join(models.Artist, models.Artist.artist_id == models.SongArtist.artist_id)   # ← (3)
        .where(models.SongArtist.song_id.in_(song_ids))                                # ← (2)
    ...

def list_songs(db: Session, genre_id=None, artist_id=None, q=None,
               limit=None, offset=None) -> list[dict]:
    stmt = select(models.Song)
    if genre_id is not None:
        stmt = stmt.where(models.Song.genre_id == genre_id)
    if artist_is is not None:                                                          # ← (1)
        stmt = stmt.where(models.Song.id.in_(
            select(models.SongArtist.song_id).where(models.SongArtist.artist_id == artist_id)))
    if q:
        stmt = stmt.where(models.Song.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(models.Song.title).limit(limit).offset(offset)                # ← (4)
```

| # | Dónde | Qué pasa | Arreglo |
|---|---|---|---|
| 1 | `list_songs`: `if artist_is is not None` | Typo. Es el que da `NameError` en los 7 tests; como falla antes de ejecutar nada, **tapa los otros errores** | `artist_id` |
| 2 | `_to_out`: `.in_(song_ids)` | `song_ids` no existe; lo definido arriba es `genre_ids` | `.in_([s.id for s in songs])` |
| 3 | `_to_out`: `.join(models.Artist, models.Artist.artist_id == ...)` | `Artist` no tiene columna `artist_id`; su PK es `id` | `models.Artist.id == models.SongArtist.artist_id` |
| 4 | `list_songs`: `.order_by(models.Song.title)` | Los tests esperan orden por id (`Uno, Dos, Tres`); por título sale `Dos, Tres, Uno` | `models.Song.id` |

El #4 no daba error de Python: con #1 a #3 arreglados **todavía fallaban 5 tests por el orden** (`5 failed, 2 passed`), y solo al cambiarlo pasan los 7. Los fallos de `filter_by_genre`, `pagination` y artista eran por el orden, no por la lógica del filtro.

Comentario del tutor: "Repasa tus propios errores en este paso: son typos y nombres de columnas, no de lógica. El diseño del `IN (subquery)` y del lote lo hiciste bien."

Estado del repo (con el nombre ya sin guion bajo, porque otro módulo lo reutiliza; ver [[lesson-6]]):

```python
def to_out(db: Session, songs: list[models.Song]) -> list[dict]:
    if not songs:
        return []

    # consulta 2: generos de todas las canciones de la pagina
    genre_ids = [s.genre_id for s in songs]
    genres = {
        g.id: g for g in db.scalars(select(models.Genre).where(models.Genre.id.in_(genre_ids)))
    }

    # consulta 3: artistas de todas las canciones con su rol
    rows = db.execute(
        select(models.SongArtist.song_id, models.SongArtist.artist_id, models.Artist.name, models.SongArtist.role)
        .join(models.Artist, models.Artist.id == models.SongArtist.artist_id)
        .where(models.SongArtist.song_id.in_([s.id for s in songs]))
        .order_by(models.SongArtist.song_id, models.SongArtist.artist_id)
    ).all()

    by_song = defaultdict(list)
    for r in rows:
        by_song[r.song_id].append({"artist_id": r.artist_id, "name": r.name, "role": r.role})

    return [
        {
            "id": s.id, "title": s.title, "duration_s": s.duration_s,
            "created_at": s.created_at, "genre": genres[s.genre_id],
            "artists": by_song[s.id],
        }
        for s in songs
    ]


def list_songs(db: Session, genre_id=None, artist_id=None, q=None, limit=None, offset=None) -> list[dict]:
    stmt = select(models.Song)
    if genre_id is not None:
        stmt = stmt.where(models.Song.genre_id == genre_id)
    if artist_id is not None:
        stmt = stmt.where(
            models.Song.id.in_(
                select(models.SongArtist.song_id)
                .where(models.SongArtist.artist_id == artist_id)
            )
        )
    if q:
        stmt = stmt.where(models.Song.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(models.Song.id).limit(limit).offset(offset)
    return to_out(db, list(db.scalars(stmt)))
```

> 📝 En el repo `limit=None, offset=None` son los valores por defecto del repositorio (sin paginar); la paginación por defecto de 20 vive en el router (`Query(20, ...)`). SQLAlchemy trata `.limit(None)` como "sin límite".

Y el router:

```python
@router.get("", response_model=list[SongsOut])
def list_songs(
    db: Session = Depends(get_db),
    genre_id: int | None = None,
    artist_id: int | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
    return songs
```

(En esta primera versión el usuario dejó un bloque `if songs is None or []: raise HTTPException(...)`; se explicó y se eliminó más tarde — ver 3A.19.)

Resultado: "excelente, tenemos verde".

---

### 2A.7 `GET /artists/{artist_id}/songs` (casi todo se reutiliza)

El test pide: `/artists/2/songs` devuelve `["Uno", "Tres"]` y "Uno" mantiene **sus 2 artistas** (si se filtrara con JOIN quedaría solo 1); `/artists/999/songs` devuelve 404.

No hay SQL nuevo; hay dos decisiones:

1. **Reutilizar `list_songs(db, artist_id=...)`**, que ya hace el `IN (subquery)` y el lote de artistas.
2. **El 404 lo decide el router** (concepto HTTP), igual que en `get_artist`. Para saber si el artista existe se usa `artists_repo.get_artist(db, artist_id)`, que ya devuelve `None` si no existe.

```python
from app.repositories import songs as songs_repo   # import que se añade

@router.get("/{artist_id}/songs", response_model=list[SongsOut])
def get_artist_songs(artist_id: int, db: Session = Depends(get_db)):
    if artists_repo.get_artist(db, artist_id) is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found.")
    return songs_repo.list_songs(db, ...)      # hueco: artist_id=artist_id
```

Dos puntos a revisar que se comentaron:

- **El límite.** `list_songs` tiene `limit=None, offset=None` por defecto → aquí devuelve **todas** las canciones del artista, sin paginar. Sirve para este endpoint; se puede añadir `limit`/`offset` como en `GET /songs` si se quiere paginar (los tests no lo exigen).
- **Coste.** `get_artist` hace sus propias consultas (artista + géneros) solo para saber si existe. Alternativa: `db.get(models.Artist, artist_id)` (una consulta), pero entonces el router importa `models` y salta la capa de repositorio. "Elige tú y puedes defender cualquiera de las dos."

Versión del repo (usuario):

```python
@router.get("/{artist_id}/songs", response_model=list[SongsOut])
def get_artist_songs(artist_id: int, db: Session = Depends(get_db)):
    if artists_repo.get_artist(db, artist_id) is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found.")
    songs = songs_repo.list_songs(db=db, artist_id=artist_id)
    if songs is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} songs not found.")
    return songs
```

> 📝 Observación sobre el repo actual: el segundo `if songs is None` (y el `if artists is None` de `GET /artists`) son **código muerto**: `list_songs` y `list_artists` siempre devuelven una lista (posiblemente vacía), nunca `None`. Ver 3A.19.

Test: `uv run pytest tests/test_catalog_api.py -k artist_songs -q`. Resultado: verde ("tenemos verde que sigue").

---

### 2A.8 Paso 5 — El formato de error unificado (exception handlers en `main.py`)

**Por qué hace falta.** FastAPI responde los errores con formas distintas:

- `HTTPException` (404, 401…) → `{"detail": "Song 999 not found"}`.
- Error de validación (422) → `{"detail": [ {...}, {...} ]}`, una **lista**.

Un cliente (como el futuro React) no debería adivinar la forma. El README fija una sola:

```json
{"error": {"code": "not_found", "message": "Song 7 not found"}}
```

con códigos `validation_error`, `unauthorized`, `not_found`, `conflict`, `internal_error` (y "también el 500").

**Cómo se hace.** Se registran dos *exception handlers* en la app: uno para `HTTPException` y otro para `RequestValidationError`; ambos devuelven un `JSONResponse` con el mismo formato.

**Esqueleto entregado** (con tres decisiones para el usuario):

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

CODES = {401: "unauthorized", 404: "not_found", 409: "conflict", 422: "validation_error"}


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = CODES.get(exc.status_code, ...)      # ¿qué código das a un status que no está en el dict?
    return JSONResponse(status_code=exc.status_code, content=error_body(code, ...))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", ...),   # ¿qué pones de mensaje?
    )
```

Las tres decisiones:

1. **Registrar el handler de *Starlette*, no el de FastAPI.** El de FastAPI es una **subclase**: atrapa solo lo que lanza tu código. El de Starlette atrapa también el 404 de una ruta que no existe o el 405.
2. **Código por defecto** para un status que no esté en `CODES`. El README dice `internal_error` para el 500, aunque los 500 reales los atrapa otro mecanismo.
3. **Mensaje en validación.** `exc.errors()` es una lista de dicts con `loc`, `msg` y `type`. Se puede mandar un texto resumido (el primer error) o dejar el `message` corto y añadir un campo `details`. Al test le basta `code == "validation_error"`.

**Pedido del usuario:** *"Estoy muy familiarizado con esta anotación que me estás mostrando. Entonces, por ahora, dame la solución y explícame un poco cómo funciona este decorador, qué son esos `request` y `exc` argumentos."* (📝 El texto dictado dice "Estoy muy familiarizado", pero el resto del mensaje —"no sabría decirte"— indica que quiso decir "no estoy muy familiarizado"; se respondió con solución + explicación.)

**Typos en sus imports** (su `main.py` ya tenía los imports pegados, pero con una letra mal; toda la suite se caía porque `main.py` no importaba):

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError      # tenía "fastappi"
from fastapi.responses import JSONResponse                 # tenía "dastapi"
from starlette.exceptions import HTTPException as StarletteHTTPException
```

Error visible: `ModuleNotFoundError: No module named 'fastappi'`.

**Solución (la que está hoy en `app/main.py`):**

```python
CODES = {401: "unauthorized", 404: "not_found", 409: "conflict", 422: "validation_error"}


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = CODES.get(exc.status_code, "internal_error")
    return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    where = ".".join(str(p) for p in first["loc"])
    return JSONResponse(status_code=422, content=error_body("validation_error", f"{where}: {first['msg']}"))
```

Resultado real (probado en copia con tablas creadas):

```
GET  /songs/999     → 404 {"error": {"code": "not_found", "message": "Song 999 not found"}}
GET  /songs?limit=0 → 422 {"error": {"code": "validation_error", "message": "query.limit: Input should be greater than or equal to 1"}}
GET  /nada          → 404 {"error": {"code": "not_found", "message": "Not Found"}}
POST /health        → 405 {"error": {"code": "internal_error", "message": "Method Not Allowed"}}
```

Suite completa con la solución: **46 passed, 1 skipped**.

**Cómo funciona el decorador** (explicación dada):

`@app.exception_handler(X)` es el mismo patrón que `@app.get("/health")`: **registra una función en la app**. La diferencia es qué la dispara.

- `@app.get("/health")`: "cuando llegue un GET a `/health`, llama a esta función".
- `@app.exception_handler(StarletteHTTPException)`: "cuando cualquier endpoint lance esta excepción, llama a esta función en vez de dejar que FastAPI responda por defecto".

Es decir, `raise HTTPException(404, "Song 999 not found")` en el router **ya no genera la respuesta directamente**: FastAPI atrapa la excepción, busca un handler registrado para ese tipo y devuelve lo que ese handler construya. Sin handler, usa su formato por defecto (`{"detail": ...}`).

**Qué son `request` y `exc`:** FastAPI llama al handler y le pasa siempre dos argumentos, por posición.

- **`request`**: la petición HTTP que provocó el error (URL, headers, método, cliente). Aquí no se usa, pero tiene que estar en la firma porque FastAPI lo pasa siempre. Sirve, p. ej., para registrar en un log qué ruta falló.
- **`exc`**: la excepción lanzada, ya como objeto (abreviatura habitual de *exception*). De ahí salen los datos para armar la respuesta:
  - En el handler de `StarletteHTTPException`: `exc.status_code` (404) y `exc.detail` (`"Song 999 not found"`, el texto que se puso en el router).
  - En el de `RequestValidationError`: `exc.errors()`, lista de dicts con `loc` (p. ej. `("query", "limit")`), `msg` y `type`.
- Los `: Request` y `: StarletteHTTPException` son **solo anotaciones de tipo**. Ayudan al editor, pero FastAPI no los usa para decidir qué pasar: lo que decide qué excepción atrapa cada handler es el **argumento del decorador**.

**Detalles de la solución:**

- **`async def`**: los handlers de excepciones en FastAPI son `async` por convención. Aquí no hay I/O, así que da igual.
- **Starlette y no el `HTTPException` de FastAPI**: ver decisión 1.
- **`CODES.get(status, "internal_error")`**: `.get` devuelve el valor por defecto si el status no está en el dict.
- **Un fallo del contrato:** un `POST /health` da un **405** con el código `internal_error`, engañoso (un 405 no es un error del servidor). Se puede añadir `405: "method_not_allowed"` a `CODES`. No afecta a los tests; decide el usuario.
- **Qué falta:** los **500 reales** (excepción no controlada) no pasan por este handler y salen con el formato por defecto. El README promete también el formato para el 500. Se arregla con un tercer handler para `Exception` que devuelva `internal_error`. Opcional; no lo piden los tests.
- `test_stubs_answer_501` sigue pasando: los handlers cambian el cuerpo, no el status.

El usuario: "estamos en verde". Lección 5 (parte de lectura) cerrada.

---

### 2A.9 Cierre de la parte A y limpieza

Limpieza que se pidió (5 min):

1. En `seed.py` línea 14, quitar `song_ids`: `genre_ids, artist_ids = {}, {}` (variable sobrante de [[lesson-3]]).
2. En `repositories/artists.py` línea 35, tipo de retorno `-> dict | None` en `get_stats`.
3. Marcar en el README los tres primeros puntos de "Orden de construcción" y corregir la tabla de `genres` (ahora tiene `created_at`).
4. Revisar que exista un `.gitignore` con `.venv/`, `__pycache__/` y `data/*.db` (el tutor no lo encontró ni en `backend/` ni en la raíz al mirar en ese momento, aunque las notas del usuario en [[lesson-1]] describen cómo crearlo; conviene comprobar que está y que cubre `backend/data/*.db`).
5. Hacer el commit.

Evolución de la suite durante la parte A (tests totales 46–47, con `1 skipped`):

| Momento | Resultado |
|---|---|
| Tests entregados, antes de implementar nada | `19 failed, 26 passed, 1 skipped` |
| Con la solución de referencia (copia) | `45 passed, 1 skipped` (46 total) |
| Tras el paso 0, antes de cablear el paso 1 (`-k "genres or models"`) | `2 failed, 14 passed` (`test_list_genres` con 501 y `test_get_artist_with_genres`: el patrón `genres` también engloba un test de artistas) |
| WIP del usuario con `Session` mal importada | colección rota: `2 errors during collection` |
| Tras arreglar imports y `Depdends` | `28 passed, 1 skipped` (filtrado) |
| Tras 4a | `14 failed, 31 passed, 1 skipped` |
| Tras 4b (+1 test por orden por nombre = 47 total) | `13 failed, 33 passed, 1 skipped` |
| Tras 4c (stats) | `10 failed, 36 passed, 1 skipped` |
| Con `list_songs` roto (typos) | `10 failed` (`NameError`) |
| Tras `list_songs` y `/artists/{id}/songs` | solo quedan los 2 tests del sobre de errores |
| Tras el sobre de errores | **46 passed, 1 skipped** |
| Con los 14 tests de auth (referencia) | 60 passed, 1 skipped (ver [[lesson-4]]) |

#### Balance de tiempo y herramientas anti-typos (conversación al cierre)

Pregunta del usuario: *"hoy en dos lecciones tomamos todo el día, aproximadamente 3 h por cada una, ¿cuánto crees que nos tome esta lección [auth]?"* Estimación del tutor: **1 h 45 min a 2 h 15 min** (menos que las de hoy). Y la observación clave: *lo que más tiempo quitó hoy fueron los **typos**, no los conceptos* (`artist_is`, `song_ids`, `fastappi`, `Depdends`). Dos comandos de un segundo cada uno lo evitan:

```bash
cd backend && uvx ruff check app tests          # atrapa nombres no definidos (artist_is, song_ids)
uv run python -c "import app.main"              # atrapa imports mal escritos (fastappi)
```

"Córrelos antes de pytest." (Más adelante la comprobación se afinó a `uvx ruff check --select F,E9 app tests`.) Regla del tiempo: si el paso 4 de la lección siguiente pasa de 40 minutos, pedir la solución y seguir.

#### Barra de progreso que pidió el usuario

*"Muéstrame una barra de progreso de este proyecto de entrenamiento y qué tópicos nos faltan por ver."* Respuesta del tutor (estado tras esta lección):

```
Backend núcleo   ████████████░░░░░░░░  60%  (6/10)
Frontend         ░░░░░░░░░░░░░░░░░░░░   0%  (0/2)
Entrevista       ░░░░░░░░░░░░░░░░░░░░   0%  (0/3)
Extras           ░░░░░░░░░░░░░░░░░░░░   0%  (0/2)   recortables
Total            ███████░░░░░░░░░░░░░  35%  (6/17 temas)
```

Por horas de trabajo estimadas, ≈45 % (estimación del tutor). Ya visto: entorno y `/health`, contrato de schemas y routers, modelos SQLAlchemy con DB y seed, repositorios con SQL (`JOIN`, `IN`, N+1, paginación), tests con TestClient y fixtures, y el formato de error unificado. Faltaba, en este orden: Auth (~2 h), `POST /artists` y `POST /songs` (~45 min), Playlists (~2–2,5 h), Service layer y patrones (~30 min), React (~2 h), diseño de streaming (~1,5 h), narrativa de experiencia (~45 min), simulacro de 90 min, pandas+NumPy (~1 h, recortable) y Dockerfile (~30 min, recortable). También se apuntó lo que **no** está en la lista y puede salir: preguntas básicas de backend (verbos HTTP, idempotencia, `async` vs `def` en FastAPI, índices, transacciones, migraciones con Alembic) y de frontend (hooks, `key` en listas, levantar el estado).

---

## 2B · Paso a paso — escrituras protegidas y capa de servicio

> **Qué cubre esta mitad:** `POST /artists` y `POST /songs`, los dos únicos endpoints de escritura del catálogo. Es la primera vez que `current_user` protege un endpoint real, y la primera vez que aparece una **capa de servicio** (`services/`). Al final se cierra una limpieza pendiente de `GET /songs` (lista vacía = `200 []`).
>
> **Leyenda de marcas en esta parte:** 🔬 = lo comprobé al redactar estas notas (no ocurrió en clase). 📝 = observación sacada del estado actual del repo, no del diálogo. Todo lo demás sale del diálogo de clase (23 y 24 de octubre).

### 2B.0 Punto de partida

Venías de cerrar la autenticación ([[lesson-4]]): `security.py`, `depends.py` (`bearer`, `current_user`), `repositories/users.py`, `routers/auth.py` y `routers/users.py`. Antes de empezar había **una limpieza pendiente** que no era de esta lección pero bloqueaba la suite en verde:

```python
# tests/test_contract.py  (test_stubs_answer_501)
assert client.get("/me").status_code == 501      # ← borrar: /me ahora responde 401 sin token
```

El test fallaba así (lo que se vio en clase):

```
E       AssertionError: assert 401 == 501
E        +  where 401 = <Response [401 Unauthorized]>.status_code
FAILED tests/test_contract.py::test_stubs_answer_501 - AssertionError: assert...
1 failed, 2 passed
```

Se borra solo esa línea. El `assert client.get("/playlists").status_code == 501` se queda: las playlists siguen siendo un stub hasta [[lesson-6]], y entonces el test entero se borra.

**Dos ajustes al contrato del README** que salieron al escribir los tests (no estaban en la tabla original):

| Endpoint | Antes | Ahora | Por qué |
|---|---|---|---|
| `POST /artists` | 401, 422 | 401, **409**, 422 | `Artist.name` es `UNIQUE` en el modelo; sin comprobarlo, un nombre repetido sería un 500 |
| `POST /songs` | 401, 404 artista o género, 422 | igual, pero el **422 incluye "mismo `artist_id` repetido"** | la PK `(song_id, artist_id)` de `song_artists` no admite duplicados; sin cortarlo antes sería un `IntegrityError` → 500 |

**El plan que se dio** (con tiempos y la regla de la casa: *si pasas de ~40 min, pide la solución*):

| Paso | Qué haces | Tiempo estimado |
|---|---|---|
| 1 | `POST /artists` (repo y router) | 15 a 20 min |
| 2 | `POST /songs`: schema (A), repo (B), service (C), router (D) | 35 a 45 min |

Bitácora real de la sesión (hora del diálogo, 23-oct):

| Hora | Qué pasó |
|---|---|
| 17:07 | Suite en verde del usuario → reviso el repo, encuentro el test de `/me` en rojo |
| 17:08 | Escribo `test_write_api.py` (16 tests), lo valido con implementación de referencia + 6 mutaciones |
| 17:09 | Entrego Paso 1 (`POST /artists`) |
| 17:22 | Usuario: `ImportError: cannot import name 'current_user' from 'app.security'` |
| 17:23 | "tenemos los cinco en verde" |
| 17:24 | Entrego Paso 2 completo (A, B, C, D) y su estructura de capas |
| 17:35 | Usuario pega su `SongCreate` con `...` → descubrimos que el validador no estaba en el archivo |
| 17:39–17:44 | Dos preguntas sobre `field_validator` y `@classmethod` (ver 3B.4) |
| 17:46 | Tests del Paso B (`test_songs_write_repo.py`, 5) |
| 17:56 | "tenemos verde en estos tests" → Paso C con `test_songs_service.py` (5) |
| 18:06 | "tenemos verde" → Paso D (router) |
| 18:09 | Usuario: 6 tests fallan con 501 → stub duplicado |
| 18:19 | "tenemos todo en verde ahora" (92 passed, 1 skipped) |

### 2B.1 Los tests primero: `tests/test_write_api.py` (16 tests)

Como en todas las lecciones, **el tutor escribe los tests y el usuario escribe el código**. Los tests se validaron en una copia temporal del repo con una **implementación de referencia** (la solución completa) y con **mutaciones** (romper el código a propósito para comprobar que algún test lo detecta). No se tocó tu código.

Cabecera del archivo (fixtures y helper):

```python
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
```

Qué enseña esta cabecera:

- **`auth_header(client)`** reutiliza los endpoints de [[lesson-4]] (`/auth/register` y `/auth/login`) para conseguir un token real, igual que haría un cliente. Así los tests de escritura ejercitan toda la cadena de autenticación.
- **`base`** inserta datos directamente con `db_factory` (la fábrica de sesiones de `conftest.py`, SQLite en archivo temporal) porque **el contrato no tiene `POST /genres`**: no hay otra forma de crear un género, así que el test lo siembra.
- **`SONG`** es el cuerpo válido de referencia. Los tests lo modifican con `{**SONG, "genre_id": 99}` (sintaxis de "copia el diccionario y sobrescribe esta clave").

Los 16 tests y qué protege cada uno:

| # | Test | Qué protege |
|---|---|---|
| 1 | `test_create_artist_requires_auth` | sin token → `401` y `error.code == "unauthorized"` |
| 2 | `test_create_artist` | `201`, `id == 1`, `genres == []` (artista nuevo sin canciones), existe `created_at` |
| 3 | `test_created_artist_is_visible_in_reads` | lo escrito se puede leer luego con `GET /artists/{id}` y `GET /artists` |
| 4 | `test_create_artist_duplicate_name_is_409` | mismo nombre dos veces → `409` y `code == "conflict"` |
| 5 | `test_create_artist_empty_name_is_422` | `{"name": ""}` → `422` |
| 6 | `test_create_song_requires_auth` | sin token → `401` |
| 7 | `test_create_song` | `201`; cuerpo con `genre.name == "Rock"` y `artists` con nombre y rol |
| 8 | `test_created_song_is_visible_in_reads` | `GET /songs/1` devuelve **exactamente lo mismo** que devolvió el POST; y `GET /artists/2/songs` lista la canción (el artista *featured* también cuenta) |
| 9 | `test_create_song_unknown_genre_is_404` | género 99 → `404`, `code == "not_found"`, el `99` aparece en el mensaje |
| 10 | `test_create_song_unknown_artist_is_404` | artista 77 → `404` y el `77` aparece en el mensaje |
| 11 | `test_failed_create_leaves_no_song_behind` | si falla (artista 99 inexistente) **no queda ninguna canción**: `GET /songs` sigue siendo `[]` |
| 12–16 | `test_create_song_invalid_body_is_422` × 5 (parametrizado) | `no-artists` (lista vacía), `bad-role` (`"dj"`), `zero-duration` (`0`), `empty-title` (`""`), `duplicate-artist` (mismo `artist_id` dos veces) → `422` y `code == "validation_error"` |

El parametrizado usa `ids=[...]` para que pytest muestre nombres legibles (`...invalid_body_is_422[duplicate-artist]`) en lugar de `change0`, `change1`…:

```python
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
```

**Validación de los tests con mutaciones** (resultado real, sobre los 16 tests con la referencia):

| Mutación (rompo el código a propósito) | Resultado (real) | Qué test la detecta (📝 = deducido por lógica; el diálogo solo dio el recuento) |
|---|---|---|
| `POST /artists` sin `dependencies=[Depends(current_user)]` | 1 failed, 15 passed | #1: vigila la auth |
| `POST /songs` sin auth | 1 failed | #6: vigila la auth |
| 409 invertido (`is not None` → `is None`) | 2 failed, 14 passed | 📝 #2 y #3 (el primer alta ya devolvería 409); el #4 sigue pasando porque ambas peticiones dan 409 |
| `create_song` sin `commit` | 1 failed | 📝 #8: otra sesión no ve la canción sin commit (en #7 la misma sesión sí la ve) |
| service sin comprobar artistas existentes | 2 failed | 📝 #10 y #11 |
| service sin comprobar género existente | 1 failed | 📝 #9 |

Con la implementación de referencia: `16 passed` y suite completa **`82 passed, 1 skipped`**.

### 2B.2 Paso 1 — `POST /artists`

**Esqueleto que se dio** (los `...` son huecos que debe rellenar el usuario, no código):

```python
# repositories/artists.py
def get_by_name(db: Session, name: str) -> models.Artist | None:
    return db.scalar(select(models.Artist).where(models.Artist.name == ...))


def create_artist(db: Session, name: str) -> dict:
    artist = models.Artist(name=...)
    db.add(artist)
    db.commit()
    return ...(db, artist.id)       # ¿qué función que ya tienes devuelve el dict con "genres"?
```

```python
# routers/artists.py   (+ import: from app.depends import current_user)
@router.post("", status_code=201, response_model=ArtistsOut, dependencies=[Depends(...)])
def create_artist(body: ArtistsCreate, db: Session = Depends(get_db)):
    if artists_repo.get_by_name(db, body.name) is not ...:
        raise HTTPException(status_code=..., detail=f"Artist {body.name!r} already exists")
    return artists_repo.create_artist(db, ...)
```

**Versión final del usuario (en el repo):**

```python
# repositories/artists.py
def get_by_name(db: Session, name: str) -> models.Artist | None:
    return db.scalar(select(models.Artist).where(models.Artist.name == name))


def create_artist(db: Session, name: str) ->dict:
    artist = models.Artist(name=name)
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return get_artist(db=db, artist_id=artist.id)
```

```python
# routers/artists.py
from app.depends import current_user

@router.post("", status_code=201, response_model=ArtistsOut, dependencies=[Depends(current_user)])
def create_artist(body: ArtistsCreate, db: Session = Depends(get_db)):
    if artists_repo.get_by_name(db=db, name=body.name) is not None:
        raise HTTPException(status_code=409, detail=f"Artist {body.name!r} already exists")
    return artists_repo.create_artist(db=db, name=body.name)
```

📝 Diferencia respecto al esqueleto: el usuario añadió `db.refresh(artist)` (el mismo patrón que ya usó en `create_user` de [[lesson-4]], donde se explicó que `refresh` relee `id` y `created_at`, que genera la base) y pasó los argumentos con nombre (`db=db, name=...`). Ambas cosas son válidas.

**Qué se practica en este paso** (la explicación de clase):

- **`dependencies=[Depends(current_user)]` en el decorador.** Exige un token válido pero **no te entrega el usuario**. Se usa cuando solo necesitas el *permiso* ("¿hay alguien autenticado?"), como aquí. Cuando necesites saber *quién* es (p. ej. el dueño de una playlist), se usa el parámetro `user: models.User = Depends(current_user)` (eso llega en [[lesson-6]]).
- **Reusar `get_artist` dentro de `create_artist`.** `genres` es un campo **calculado**, no se guarda en la tabla `artists`. Para un artista recién creado es `[]`, y la función que ya existía lo resuelve sin código nuevo.
- **El 409 y el `UNIQUE`.** Se comprueba el nombre *antes* para dar un error claro (`409 conflict`). La restricción `UNIQUE` de la base es la **última defensa** si dos peticiones llegaran a la vez, igual que en `register`.

**Cómo se comprobó:**

```bash
cd backend
uvx ruff check --select F,E9 app tests          # nombres no definidos, imports sin usar
uv run python -c "import app.main"              # la app importa sin romperse
uv run pytest tests/test_write_api.py -k "create_artist or created_artist" -q
```

Salida buscada: **`5 passed`**. El filtro `-k "create_artist or created_artist"` selecciona por subcadena en el nombre del test; coge los 5 tests de artistas (#1–#5) y **ninguno** de canciones (`create_song…`). Hay que vigilar los nombres: un `-k` demasiado corto puede colarse en tests ajenos.

### 2B.3 El error del import (primera caída del usuario)

Al probar, el usuario pegó:

```
File ".../app/routers/artists.py", line 8, in <module>
    from app.security import current_user
ImportError: cannot import name 'current_user' from 'app.security'
```

Diagnóstico: importó `current_user` del módulo equivocado. Cada módulo tiene su contenido:

| Módulo | Qué tiene |
|---|---|
| `security.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_access_token` |
| `depends.py` | `bearer`, `current_user` |

Arreglo: `from app.depends import current_user`. El mensaje se lee: *"busqué `current_user` dentro de `app.security` y no está"*. Causa típica: nombre mal escrito o módulo equivocado.

**Lección de herramienta:** este es justo el tipo de error que **`ruff` con `--select F,E9` no detecta** (ruff no abre el otro módulo para ver si el nombre existe) y que **`uv run python -c "import app.main"` sí detecta**. Por eso el bloque de comprobación siempre lleva las dos cosas. Tras el arreglo: **5 passed**.

### 2B.4 Paso 2 — `POST /songs`, la arquitectura por capas

Es el endpoint más completo del proyecto. Crear una canción implica cuatro cosas a la vez:

1. Comprobar que el género existe.
2. Comprobar que **todos** los artistas existen.
3. Insertar la canción y sus vínculos con los artistas **en una sola transacción**: o se guarda todo, o nada.
4. Devolver la canción completa.

Por eso aparece el **service layer**. Cada capa hace una sola cosa:

```
router     → HTTP: auth, 201 / 404          (no sabe SQL)
service    → reglas de negocio              (no sabe HTTP: lanza una excepción propia)
repository → SQL                            (no sabe de reglas)
```

Las reglas del tipo "¿existe el género?" no son SQL ni HTTP; eso es lo que justifica una capa propia. Primer paso: crear `app/services/__init__.py` vacío, igual que tiene `repositories/`.

**Flujo completo de una petición `POST /songs`:**

```
POST /songs  (Authorization: Bearer …, body JSON)
  FastAPI resuelve dependencias ANTES de ejecutar create_song():
      current_user (decorador) → token inválido o ausente → 401   (no se llega a validar el cuerpo)
      get_db                   → entrega la Session
  Pydantic valida el cuerpo → SongCreate (tipos, Field, field_validator) → si falla → 422
  create_song(router) → songs_service.create_song(db, body)
        service: genre_exists?  no → RelatedNotFound ─────────────┐
                 existing_artist_ids → faltan? → RelatedNotFound ─┤ el router lo captura
                 songs_repo.create_song (flush + add_all + commit) │ y lo convierte en
                 songs_repo.get_song → dict completo               │ HTTPException(404)
  response_model=SongsOut filtra y serializa → 201                 ┘
```

#### Paso 2-A · `schemas.py`: rechazar artistas repetidos

La clave `(song_id, artist_id)` no admite duplicados. Si el cliente manda el mismo artista dos veces, la base daría un `IntegrityError` y un 500. Se corta antes, en el schema (esqueleto dado):

```python
from pydantic import BaseModel, Field, field_validator    # añade field_validator

class SongCreate(BaseModel):
    ...
    artists: list[SongArtistIn] = Field(min_length=1)

    @field_validator("artists")
    @classmethod
    def no_duplicate_artists(cls, v):
        ids = [a.artist_id for a in v]
        if len(ids) != len(...):                 # ¿cómo detectas repetidos con un set?
            raise ValueError("duplicate artist_id in artists")
        return v
```

**Versión final (en el repo):**

```python
class SongArtistIn(BaseModel):
    artist_id: int
    role: Literal["main", "featured", "producer", "writer"]


class SongCreate(BaseModel):
    title: str = Field(min_length=1)
    duration_s: int = Field(gt=0)
    genre_id: int
    artists: list[SongArtistIn] = Field(min_length=1)

    @field_validator("artists")
    @classmethod
    def no_duplicate_artists(cls, v):
        ids = [a.artist_id for a in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate artist_id in artists")
        return v
```

**Lo que pasó en clase (17:35):** el usuario pegó la clase con `...` literal:

```python
class SongCreate(BaseModel):
    ...
    artists: list[SongArtistIn] = Field(min_length=1)

    @field_validator("artists")
    ...
```

Se comprobó su archivo real: **el validador no estaba**; la clase seguía con sus tres campos y sin el método (campos del modelo: `['title', 'duration_s', 'genre_id', 'artists']`). La aclaración: **la `...` de un esqueleto no es código**, significa *"aquí van los campos que ya tienes"*. Si el usuario hubiera dejado la `...` en lugar de `title`, `duration_s` y `genre_id`, esos tres campos habrían desaparecido del modelo.

Pruebas hechas en una copia con la clase completa:

```
cuerpo válido           → pasa
artista repetido        → ('artists',) | Value error, Duplicate artist_id in artists
por la API              → 422 {'error': {'code': 'validation_error',
                                'message': 'body.artists: Value error, Duplicate artist_id in artists'}}
```

El mensaje sale por el *handler* de `main.py` (`validation_error_handler`), que concatena `loc` + `msg` del primer error: de ahí `body.artists: Value error, …`. Ver el desglose de conceptos en 3B.4–3B.6.

#### Paso 2-B · `repositories/songs.py`: tres funciones nuevas

Sin router conectado no habría *feedback* hasta el final, así que se escribieron **tests directos** para estas tres funciones (`tests/test_songs_write_repo.py`, 5 tests; en tu repo fallaban los 5 hasta implementar).

Esqueleto entregado:

```python
def genre_exists(db: Session, genre_id: int) -> bool:
    return db.get(models.Genre, genre_id) is not ...


def existing_artist_ids(db: Session, ids: list[int]) -> set[int]:
    return set(db.scalars(select(models.Artist.id).where(models.Artist.id.in_(...))))


def create_song(db: Session, title: str, duration_s: int, genre_id: int,
                artists: list[tuple[int, str]]) -> int:
    song = models.Song(title=title, duration_s=duration_s, genre_id=genre_id)
    db.add(song)
    db.flush()                    # ejecuta el INSERT dentro de la transacción: ahora song.id existe
    db.add_all([models.SongArtist(song_id=..., artist_id=a, role=r) for a, r in artists])
    db.commit()                   # un solo commit para la canción y todos sus vínculos
    return song.id
```

**Versión final del usuario:**

```python
def genre_exists(db: Session, genre_id: int) -> bool:
    return db.get(models.Genre, genre_id) is not None


def existing_artist_ids(db: Session, ids:list[int]) -> set[int]:
    return set(db.scalars(select(models.Artist.id).where(models.Artist.id.in_(ids))).all())


def create_song(db: Session, title: str, duration_s: int, genre_id: int,
                artists: list[tuple[int, str]]) -> int:
    song = models.Song(title=title, duration_s=duration_s, genre_id=genre_id)
    db.add(song)
    db.flush()
    db.add_all([
        models.SongArtist(song_id=song.id, artist_id=a, role=r) for a, r in artists
    ])
    db.commit()
    return song.id
```

Qué hace cada una:

- **`genre_exists`:** `db.get` devuelve el objeto o `None`; la función solo responde sí/no, así que compara con `None`.
- **`existing_artist_ids`:** recibe una lista de ids y devuelve **cuáles existen en una sola consulta** con `IN`. Si le pides `[1, 2, 99]` y solo existen 1 y 2, devuelve `{1, 2}`. El service resta este resultado a lo pedido para saber qué falta. Es la misma idea anti-N+1 de la parte A (una consulta para N artistas en vez de N consultas).
- **`create_song`:** `db.flush()` envía el INSERT de la canción **sin cerrar la transacción**, y eso le asigna su `id`. Ese `id` es el hueco `song_id=song.id`: sin el `flush`, `song.id` sería `None` y falla con `NOT NULL constraint failed: song_artists.song_id`. **Un solo `commit()` al final** hace permanentes la canción **y** sus vínculos a la vez.

**Los 5 tests del repo (`test_songs_write_repo.py`):**

```python
def test_genre_exists(db_factory, base): ...
def test_existing_artist_ids_returns_only_the_ones_that_exist(db_factory, base):
    with db_factory() as db:
        assert songs_repo.existing_artist_ids(db, [1, 2, 99]) == {1, 2}
        assert songs_repo.existing_artist_ids(db, [99]) == set()

def test_create_song_returns_id_and_links_every_artist(db_factory, base): ...

def test_create_song_is_committed(db_factory, base):
    with db_factory() as s1:
        songs_repo.create_song(s1, "Uno", 180, 1, [(1, "main")])
    with db_factory() as s2:                       # otra sesión, como otra petición HTTP
        assert s2.scalar(select(models.Song.title)) == "Uno"

def test_failure_midway_leaves_no_orphan_song(db_factory, base):
    """El artista 99 no existe: falla al vincular. La canción NO debe quedar guardada."""
    with db_factory() as s1:
        with pytest.raises(IntegrityError):
            songs_repo.create_song(s1, "Uno", 180, 1, [(1, "main"), (99, "featured")])
    with db_factory() as s2:
        assert s2.scalars(select(models.Song)).all() == []
        assert s2.scalars(select(models.SongArtist)).all() == []
```

Dos detalles de diseño de estos tests:

- **Para probar un `commit` se abre una segunda sesión** (`s2`) que lee lo que `s1` escribió. Es la forma de simular "otra petición HTTP": si solo hubo `flush` o no hubo `commit`, `s2` no ve nada.
- **`test_failure_midway…` fuerza un fallo a mitad** (artista 99 inexistente rompe la FK al vincular, con `PRAGMA foreign_keys=ON` activo en `db.py`) y comprueba que **ni la canción ni los vínculos quedaron guardados**. Es la prueba de **atomicidad**.

**Mutaciones sobre el repo (resultado real):**

| Mutación | Resultado | Qué lo detecta |
|---|---|---|
| dos `commit` (uno tras la canción y otro tras los vínculos) | 1 failed, 4 passed | `test_failure_midway_leaves_no_orphan_song` (la canción ya estaría guardada cuando falla el vínculo) |
| sin `flush` | 2 failed | `NOT NULL constraint failed: song_artists.song_id` |
| sin `commit` (queda `flush`) | 1 failed | `test_create_song_is_committed` |
| `existing_artist_ids` devuelve `set(ids)` (todo lo pedido) | 1 failed | `…returns_only_the_ones_that_exist` |

Comprobación del paso:

```bash
cd backend
uvx ruff check --select F,E9 app tests
uv run python -c "import app.main"
uv run pytest tests/test_songs_write_repo.py -q        # → 5 passed
```

#### Paso 2-C · `services/songs.py` (archivo nuevo)

Tests directos del servicio: `tests/test_songs_service.py` (5 tests, **sin HTTP**).

Esqueleto entregado:

```python
from sqlalchemy.orm import Session

from app.repositories import songs as songs_repo
from app.schemas import SongCreate


class RelatedNotFound(Exception):
    """El género o algún artista de la canción no existe."""


def create_song(db: Session, body: SongCreate) -> dict:
    if not songs_repo.genre_exists(db, body.genre_id):
        raise RelatedNotFound(f"Genre {body.genre_id} not found")

    ids = [a.artist_id for a in body.artists]
    missing = sorted(set(ids) - songs_repo.existing_artist_ids(db, ...))
    if missing:
        raise RelatedNotFound(f"Artist(s) {missing} not found")

    song_id = songs_repo.create_song(
        db, body.title, body.duration_s, body.genre_id,
        [(a.artist_id, a.role) for a in body.artists],
    )
    return songs_repo....(db, song_id)
```

**Versión final del usuario (en el repo):**

```python
class RelatedNotFound(Exception):
    """El género o algún artista de la canción no existe."""


def create_song(db: Session, body: SongCreate) -> dict:
    if not songs_repo.genre_exists(db, body.genre_id):
        raise RelatedNotFound(f"Genre {body.genre_id} not found")

    ids = [a.artist_id for a in body.artists]
    missing = sorted(set(ids) - songs_repo.existing_artist_ids(db=db, ids=ids))
    if missing:
        raise RelatedNotFound(f"Artist(s) {missing} not found")

    song_id = songs_repo.create_song(
        db=db,
        title=body.title,
        duration_s=body.duration_s,
        genre_id = body.genre_id,
        artists=[(a.artist_id, a.role) for a in body.artists]
    )
    return songs_repo.get_song(db, song_id)
```

Cómo se lee cada bloque (explicación de clase):

- **`class RelatedNotFound(Exception)`:** una excepción propia, vacía. Sirve de **señal entre capas**: el service dice "algo relacionado no existe" **sin saber qué es un 404**. Quien la reciba decide qué hacer. Hoy es el router; mañana podría ser un script o una tarea en segundo plano.
- **`ids = [...]`:** extrae solo los `artist_id` del body, que es lo que necesita `existing_artist_ids`.
- **`set(ids) - existing`:** resta de conjuntos. *Lo pedido menos lo que existe = exactamente lo que falta.* El `sorted` deja el mensaje estable (`[77, 99]`) sin depender del orden interno de un `set`.
- **El orden de las comprobaciones:** se valida **todo antes** de llamar a `create_song`. Si falta el género o un artista se lanza la excepción y **no se escribe nada** (`test_nothing_is_written_when_validation_fails`).
- **La última línea** reutiliza `get_song` (la misma función de `GET /songs/{id}`) y devuelve la canción completa con `genre` y artistas con rol.
- **Este archivo no importa FastAPI.** Si lo hiciera, la capa de servicio quedaría atada a HTTP. Un test lo vigila (ver abajo).

**Los 5 tests del service:**

| Test | Qué protege |
|---|---|
| `test_create_song_returns_the_full_song` | devuelve el dict completo: `id == 1`, `genre.name == "Rock"`, artistas con su rol |
| `test_unknown_genre_raises_related_not_found` | `pytest.raises(RelatedNotFound, match="99")` |
| `test_all_unknown_artists_are_reported_sorted` | artistas `[99, 1, 77]` → mensaje con `[77, 99]` (**todos** los que faltan, ordenados) |
| `test_nothing_is_written_when_validation_fails` | tras fallar por género y por artista, `select(Song)` sigue vacío |
| `test_service_does_not_know_about_http` | analiza el código fuente con `ast` y exige que `fastapi` y `starlette` **no** estén importados |

El último es un **test de arquitectura**: en vez de probar un comportamiento, prueba una regla de diseño.

```python
def test_service_does_not_know_about_http():
    """La capa de servicio no importa FastAPI: lanza su propia excepción y el router decide el 404."""
    tree = ast.parse(inspect.getsource(songs_service))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
    assert "fastapi" not in imported and "starlette" not in imported
```

**Mutaciones sobre el service (resultado real) y la que "sobrevivió":**

| Mutación | Resultado |
|---|---|
| sin chequeo de género (`if False:`) | 2 failed, 3 passed |
| sin chequeo de artistas (`if False:`) | 2 failed, 3 passed |
| devuelve `{'id': song_id}` en vez de la canción | 1 failed |
| añade `from fastapi import HTTPException` | 1 failed (el test de arquitectura) |
| faltantes **sin ordenar** (`list(set(ids) - existing)[::-1]`) | **5 passed** ← no detectada |

La mutación de orden no se detectó. En vez de dar el test por bueno, se sospechó de la propia mutación y se repitió de otra forma (faltantes en el orden en que los manda el cliente, `[99, 77]`): ahí sí falló `test_all_unknown_artists_are_reported_sorted`. 🔬 Por qué la primera sobrevivió: en CPython un `set` de enteros pequeños se recorre por su posición en la tabla hash (`n % 8` para tablas de 8 huecos): `99 % 8 = 3` y `77 % 8 = 5`, así que `list({99, 77})` da `[99, 77]`; invertido es `[77, 99]`, justo el orden de `sorted`. La mutación coincidió con la respuesta correcta por casualidad. **Lección:** un test que pasa con una mutación puede ser un test débil *o* una mutación mal elegida; hay que comprobar cuál de las dos antes de concluir.

Comprobación del paso:

```bash
cd backend
uvx ruff check --select F,E9 app tests
uv run python -c "import app.services.songs"
uv run pytest tests/test_songs_service.py -q           # → 5 passed
```

#### Paso 2-D · `routers/songs.py`: conectar el router

El router es el **único** sitio que sabe de HTTP: traduce la excepción del service en un 404. Esqueleto:

```python
from app.depends import current_user
from app.services import songs as songs_service


@router.post("", status_code=201, response_model=SongsOut, dependencies=[Depends(current_user)])
def create_song(body: SongCreate, db: Session = Depends(get_db)):
    try:
        return songs_service.create_song(db, body)
    except songs_service.RelatedNotFound as e:
        raise HTTPException(status_code=..., detail=str(e))
```

**Versión final (en el repo):** idéntica con `status_code=404`:

```python
@router.post("", status_code=201, response_model=SongsOut, dependencies=[Depends(current_user)])
def create_song(body: SongCreate, db: Session = Depends(get_db)):
    try:
        return songs_service.create_song(db, body)
    except songs_service.RelatedNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
```

Qué mirar (explicación de clase):

- **`str(e)`** devuelve el mensaje con el que se lanzó la excepción, p. ej. `Artist(s) [77, 99] not found`. Ese texto llega al cliente dentro del formato de error de `main.py`: `{"error": {"code": "not_found", "message": "Artist(s) [77, 99] not found"}}`.
- **`except` captura solo `RelatedNotFound`.** Cualquier otro error (un `IntegrityError`, por ejemplo) no se atrapa y sube como 500. Eso es lo correcto: sería un bug nuestro, no un error del cliente.
- **Es `raise`, no `return`.** Ya había mordido antes, en `depends.py` ([[lesson-4]]).
- **`dependencies=[Depends(current_user)]`** hace que sin token la respuesta sea 401, igual que en `POST /artists`.
- **Los 422** (cuerpo inválido, artistas repetidos) ya los resuelven el schema y el handler de `main.py`: no hay código nuevo para eso.

Comprobación del paso:

```bash
cd backend
uvx ruff check --select F,E9 app tests
uv run python -c "import app.main"
uv run pytest tests/test_write_api.py -q      # → 16 passed
uv run pytest -q                              # → 92 passed, 1 skipped
```

La cuenta de la suite: 82 (con todo implementado según la referencia) + 5 (repo) + 5 (service) = **92 passed, 1 skipped**.

### 2B.5 El stub duplicado: 6 fallos con 501

Al probar, el usuario adjuntó una salida con el patrón `.....FFFFFF.....` y todos los fallos eran **`501 Not Implemented`**. Se leyó su `routers/songs.py` y apareció esto:

```python
@router.post("", status_code=201,response_model=SongsOut)      # ← el stub original (3 líneas)
def create_song(body: SongCreate):
    raise HTTPException(status_code=501, detail="Not implemented")

...  # (list_songs, get_song)

@router.post("", status_code=201, response_model=SongsOut, dependencies=[Depends(current_user)])   # ← la suya, al final
def create_song(body: SongCreate, db: Session = Depends(get_db)):
    ...
```

**Dos funciones `create_song` en la misma ruta `POST /songs`.** Las dos se registran y **FastAPI usa la primera que coincide**: el stub. La función correcta que escribió al final **nunca se ejecutaba**. Es exactamente lo mismo que le pasó antes con `/me` ([[lesson-4]]). Arreglo: **borrar el stub** (las tres líneas con su decorador).

Se comprobó en una copia: solo con ese borrado pasan los **16 tests** de `test_write_api.py` y la suite da **92 passed, 1 skipped**.

Por qué el patrón `.....FFFFFF.....` tenía sentido (qué pasaba y qué no con el stub):

- Los **5 de artistas** (`.....`) ya funcionaban: `POST /artists` estaba bien.
- Los **6 que fallaban** eran los de canciones que necesitan que el endpoint *haga algo*: `requires_auth` (el stub no tenía dependencia → 501 en vez de 401), `create_song`, `created_song_is_visible`, `unknown_genre_404`, `unknown_artist_404`, `failed_create_leaves_no_song_behind`.
- Los **5 de cuerpo inválido** (`.....` finales) **pasaban aunque el endpoint fuera el stub**, porque FastAPI valida el cuerpo **antes** de ejecutar la función. Eso confirma, de paso, que el `field_validator` de artistas repetidos funcionaba.

### 2B.6 Corrección de `GET /songs` (lista vacía = `200 []`)

Al revisar el mismo archivo apareció código muerto en `list_songs` (que venía de la parte A, cuando aún no había datos de prueba):

```python
if songs is None or []:
    raise HTTPException(status_code=404, detail="No songs found")
```

Diagnóstico dado (23-oct, 18:10):

- Python lo lee como **`(songs is None) or []`**. El `[]` final siempre es falsy, así que equivale a `songs is None`. Como `songs_repo.list_songs` **siempre devuelve una lista**, la condición no se cumple nunca: **código muerto**.
- Tampoco se debe "arreglar" a `if not songs:`. Se probó y **rompe dos tests**, entre ellos `test_list_songs_combined_filters` (y `test_failed_create_leaves_no_song_behind`, que hace `client.get("/songs")` sobre una base vacía): el contrato del README dice que `GET /songs` con filtros sin resultados responde **`200` con `[]`**, no 404.
- Instrucción: **borrar esas dos líneas y devolver `songs` directamente.**

Ese consejo se malinterpretó (24-oct, 18:45): el usuario cambió el `404` por `200`:

```python
    songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
    if songs is None or []:
        raise HTTPException(status_code=200, detail="No songs found")
    return songs
```

Y la aclaración fue: **la corrección no es cambiar 404 por 200, sino borrar el `if` y el `raise`.**

```python
    songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
    return songs
```

Por qué (explicación de clase):

- **`raise HTTPException` no es para respuestas buenas.** Con `raise`, FastAPI pasa por tu manejador de errores y devolvería el **sobre de error** (`{"error": {...}}`) con código 200. Eso mezcla un error con un éxito. 📝 Mirando `main.py`: `CODES.get(exc.status_code, "internal_error")` — como `200` no está en `CODES`, el cuerpo saldría con `"code": "internal_error"` y status `200`, la peor combinación posible para un cliente.
- **Una lista vacía ya es una respuesta válida.** `return songs` con `[]` da `200 []` solo, y eso es lo que dice el contrato y lo que React espera para mostrar "no hay canciones".
- **La condición nunca fue "lista vacía"** (precedencia de `or`, ver arriba).
- `HTTPException` sigue usándose en `create_song`, así que el import se queda.

Estado actual del repo 📝: el usuario dejó las dos líneas **comentadas** (`#if songs is None or []:` / `#    raise HTTPException(status_code=200, ...)`) y `return songs`. Funciona; la recomendación final (24-oct, 18:52) fue: *"`list_songs` está bien; puedes borrar las dos líneas comentadas."*

### 2B.7 Cierre de la lección

Con `16 passed` en `test_write_api.py` y `92 passed, 1 skipped` en la suite, el cierre que se pidió:

1. Marcar `[x]` *Canciones y artistas* en el checklist de **Orden de construcción** del `README.md`.
2. Actualizar las filas del contrato: `POST /artists` con el error **409** y `POST /songs` con el **422** por artista repetido.
3. Hacer el commit (los commits los hace el usuario).

Qué dejó construido esta mitad:

| Archivo | Qué hay |
|---|---|
| `schemas.py` | `SongCreate` con `@field_validator("artists")` |
| `repositories/artists.py` | `get_by_name`, `create_artist` |
| `repositories/songs.py` | `genre_exists`, `existing_artist_ids`, `create_song` |
| `services/__init__.py` y `services/songs.py` | `RelatedNotFound`, `create_song` |
| `routers/artists.py` | `POST /artists` con 201/401/409/422 |
| `routers/songs.py` | `POST /songs` con 201/401/404/422 |
| `tests/` | `test_write_api.py` (16), `test_songs_write_repo.py` (5), `test_songs_service.py` (5) |

---

## 3A. Conceptos enseñados (parte A)

### 3A.1 Capas en el catálogo: router → repositorio → Session

- **Router (`routers/*.py`)**: capa HTTP. Recibe la request, valida parámetros (`Query`, path), llama al repositorio y **traduce `None` en 404**. No escribe SQL.
- **Repositorio (`repositories/*.py`)**: capa de datos. Recibe una `Session` y devuelve objetos del modelo o diccionarios. **No sabe de HTTP**: no lanza `HTTPException`; devuelve `None` si no encuentra.
- **Schemas (`schemas.py`)**: el "modelo de la API" (qué sale por JSON). **Models (`models.py`)**: el "modelo de la base". Son cosas distintas (por eso `ArtistsOut.genres` existe en el schema pero no en la tabla).
- Por qué: se prueba cada capa por separado y se puede cambiar la base sin tocar los routers. (La capa de *servicio* entre ambas llega en la Parte B.)

### 3A.2 `Depends(get_db)` y `dependency_overrides`

`Depends(get_db)` hace que FastAPI llame a `get_db` por request, entregue la `Session` y la cierre al terminar la respuesta (es un generador con `yield`; ver `app/db.py`). En tests, `app.dependency_overrides[get_db] = override_get_db` sustituye la dependencia por una sesión de la base temporal: **mismo router, otra base**. Es la mejor respuesta de entrevista sobre testabilidad e inyección de dependencias.

### 3A.3 `select()` describe, la `Session` ejecuta; los statements son inmutables

`select(models.Genre).order_by(...)` solo **describe** la consulta. `db.scalars(...)`, `db.execute(...)` o `db.scalar(...)` la **ejecutan**. Cada método encadenado (`.where`, `.order_by`, `.limit`) devuelve un statement **nuevo**; por eso hay que reasignar: `stmt = stmt.where(...)`. Olvidarlo hace que el filtro se pierda en silencio.

### 3A.4 `db.get` y el identity map

`db.get(Modelo, id)` es el `SELECT ... WHERE id = ?` por clave primaria; devuelve el objeto o `None`. La `Session` guarda un **mapa de identidad**: si ya cargó ese objeto, `db.get` lo devuelve **sin repetir la consulta**. Por eso `get_artist` dentro de `list_artists` no vuelve a consultar al artista (medido: 14 consultas para 13 artistas = 1 + 13 de géneros).

### 3A.5 `execute` / `scalars` / `scalar`

Ver la tabla en 2A.5. Regla: una columna o una entidad → `scalars`; varias columnas → `execute`; un solo valor (conteo, `max`) → `scalar`. `scalars` con varias columnas descarta el resto **sin avisar**.

### 3A.6 JOIN y `select_from`

`.join(Tabla, condición)` es el `JOIN tabla ON condición`. En consultas de conteo como `select(func.count())` no hay una entidad de la que partir, así que se indica con `.select_from(models.PlaylistSong)` cuál es la tabla base antes de hacer los `join`. En `select(models.Genre.name)` la tabla base se deduce de la columna.

### 3A.7 Filtros opcionales, `ilike` y `q`

- Patrón: construir `stmt = select(...)` y añadir `.where(...)` solo `if` el parámetro viene.
- Para ids: `if genre_id is not None`. Para texto: `if q:` (descarta también la cadena vacía). 📝 Razón (no dicha literalmente en el diálogo): con `is not None` solo se omite el filtro cuando el parámetro *no se envió*, y con `if q:` una búsqueda vacía equivale a no buscar.
- `ilike(f"%{q}%")` = "contiene el texto, sin distinguir mayúsculas"; en SQL es `LOWER(col) LIKE '%' || LOWER(?) || '%'` (Q2). Los `%` hacen de comodín a ambos lados.
- 📝 Nota añadida: con `%x%` el índice normal no ayuda (búsqueda secuencial); a gran escala se usaría full-text search o trigramas (`pg_trgm` en Postgres). Y un `q` que contenga `%` o `_` se interpreta como comodín.

### 3A.8 Filtrar con `IN (subconsulta)` y no con `JOIN`

Para `GET /songs?artist_id=2`: con `JOIN song_artists` la fila de la canción **se duplica** (una por artista) y el `WHERE artist_id = 2` deja fuera a los demás artistas de la canción, así que "Uno" saldría con solo Beto. Con `Song.id.in_(select(SongArtist.song_id).where(SongArtist.artist_id == X))` cada canción sale **una vez** y luego `to_out` carga *todos* sus artistas. Lo protege `test_filter_by_artist_keeps_all_artists_of_each_song`.

### 3A.9 Paginación y orden estable

- `limit` y `offset` (contrato: por defecto 20, máximo 100; `offset` ≥ 0) se validan en el router con `Query(20, ge=1, le=100)` y `Query(0, ge=0)`.
- **Siempre con `ORDER BY`**: sin orden determinista la paginación puede repetir o saltar filas. Canciones y géneros se ordenan por `id`; artistas por `name` (que es único, por tanto estable). Con una columna no única hay que añadir un desempate (`order_by(name, id)`).
- Orden en SQLite distingue mayúsculas (`func.lower(...)` si importara).
- 📝 Nota: `offset` grande es lento (la base recorre y descarta filas); la alternativa es paginación por *keyset* (`WHERE id > último_id`).

### 3A.10 El problema N+1 y el patrón de lote con `IN`

- **N+1**: 1 consulta para la lista + N consultas (una por elemento) para sus relaciones. Con 20 canciones se midieron **25 consultas** extra frente a **2** con el lote (sin contar la consulta de la lista en ninguno de los dos casos). Escala lineal con N.
- **Patrón:** (1) consulta de la página; (2) géneros con `Genre.id IN (...)`; (3) artistas con `SongArtist.song_id IN (...)`; agrupar con `defaultdict(list)` por `song_id`; montar los diccionarios de salida. `if not songs: return []` evita un `IN ()` vacío.
- Para artistas (`list_artists`) se aceptó N+1 con límite 20 y se dijo que en la entrevista se explica cómo se resolvería (una sola consulta con `IN`).
- Medición con contador de consultas: `event.listen(engine, "before_cursor_execute", hook)`.

### 3A.11 `DISTINCT`: dos cosas distintas y "el JOIN multiplica filas"

- `select(col).distinct()` → `SELECT DISTINCT col`: elimina filas repetidas **del resultado** (géneros del artista).
- `func.count(distinct(col))` → `COUNT(DISTINCT col)`: cuenta **valores distintos** de una columna (playlists).
- `select(func.count()).distinct()` → `SELECT DISTINCT count(*)`: no hace nada útil (el resultado ya es una sola fila).
- Regla: cuando un JOIN multiplica filas, cuenta con `DISTINCT` la entidad que realmente quieres contar.

### 3A.12 `func.count`, `COUNT(*)` y la PK compuesta

`func.count()` = `COUNT(*)` (cuenta filas). `song_count` no necesita `DISTINCT` porque la PK compuesta `(song_id, artist_id)` de `song_artists` impide pares repetidos (conexión con el diseño de [[lesson-3]]).

### 3A.13 Campos calculados (`ArtistsOut.genres`)

Los géneros del artista no son una columna: se **calculan** con un JOIN (`genres ← songs ← song_artists`). El repositorio devuelve un `dict` que mezcla columnas de `artists` con el resultado calculado, y las claves deben coincidir con el schema `ArtistsOut`. Mismo idea para `SongsOut.genre` (objeto anidado) y `SongsOut.artists` (lista con rol).

### 3A.14 `response_model` valida objetos ORM y diccionarios (`from_attributes` no hace falta)

FastAPI valida lo que devuelve la función contra el `response_model`, ya sea un `dict` o un objeto ORM, y lo convierte a JSON. `from_attributes` solo haría falta si se llamara a `Modelo.model_validate(obj)` a mano. Si falta un campo requerido → `ResponseValidationError` (error 500 del servidor; es un error del programador, no del cliente). Ejemplos vistos: `created_at: Field required` y `Input should be a valid list` cuando faltaba el `return`.

### 3A.15 `create_all` no altera tablas existentes (migraciones)

Añadir una columna al modelo no cambia un `music.db` ya creado. Solución en desarrollo: borrar y re-sembrar. En proyectos reales: **migraciones con Alembic**.

### 3A.16 Fixtures para probar la API con una base real

Base **en archivo** (`tmp_path`) y no `:memory:` por el hilo de `TestClient`; `sessionmaker(..., expire_on_commit=False)`; `dependency_overrides` para sustituir `get_db`; `.clear()` al terminar. El catálogo de prueba se siembra con `seed_database` y ids conocidos.

### 3A.17 Cómo se diseñan buenos tests (método)

- **Tests primero, con respuestas conocidas** (catálogo de 3 canciones).
- **Mutaciones**: romper la solución de referencia a propósito y verificar que algún test falla. Si ninguno falla, el test es débil. Ejemplo real: `test_list_artists` pasaba igual con orden por id y por nombre → se añadió `test_list_artists_is_sorted_by_name` con ids al revés.
- **Seleccionar por nombre**: `-k test_list_genres` en vez de `-k genres` (colisión de nombres).
- **Un test por regla de negocio**: "una playlist con 2 canciones de Ana cuenta 1".

### 3A.18 Errores silenciosos: `WHERE false`

`.where(Clase == valor)` compara la *clase* con el valor → `False` → `WHERE false`: la consulta no falla, devuelve `[]`. Defensas: leer el statement con `print(stmt)`; sospechar cuando un lado del `==` no lleva `.columna`; y tener tests que comparen el contenido, no solo el status.

### 3A.19 404 frente a lista vacía (`200 []`)

- Un recurso **que se pide por id** y no existe → 404 (`GET /songs/999`, `GET /artists/999/songs`).
- Una **colección filtrada que no encuentra nada** → `200` con `[]`; es una respuesta válida y es lo que React espera para mostrar "no hay canciones".
- Por eso son código muerto los `if songs is None` / `if artists is None` de los routers (los repositorios siempre devuelven una lista).
- Cuando más tarde el usuario escribió `if songs is None or []: raise HTTPException(status_code=200, ...)` se le explicó: (a) `raise HTTPException` no es para respuestas buenas, con `raise` pasa por el manejador de errores y se devolvería el sobre de error **con código 200**; (b) `songs is None or []` se lee `(songs is None) or []` y el `[]` final siempre es falso; (c) la corrección es **borrar las dos líneas** y dejar `return songs`.

### 3A.20 Sobre de errores unificado: handlers, `request`, `exc`, `CODES`

Ver 2A.8. Resumen: `@app.exception_handler(Tipo)` registra una función que se ejecuta cuando se lanza `Tipo`; recibe `request` y `exc`; hay que registrar el de **Starlette** para cubrir también los errores del framework (404 de ruta inexistente, 405); `CODES.get(status, "internal_error")` mapea status → código; el 422 de validación usa `exc.errors()` (`loc`, `msg`, `type`). Pendiente de contrato: 405 → `method_not_allowed` y handler para `Exception` (500 reales).

### 3A.21 Prevención de typos: `ruff` e importar la app

`uvx ruff check app tests` (nombres no definidos: `artist_is`, `song_ids`) y `uv run python -c "import app.main"` (imports mal escritos: `fastappi`). Correrlos antes de pytest. *(📝 No detectan typos de atributo ni de argumentos con nombre; eso se vio más tarde — ver [[lesson-8]].)*

### 3A.22 Convención `_privado` y cuándo refactorizar

El guion bajo inicial (`_genres_of`, `_to_out`) marca "función interna de este módulo". Se extrae un helper **cuando el código se duplica, no antes**; y si hay una función existente que ya sirve (`get_artist`), reutilizarla puede ser mejor que crear dos helpers. (El helper de canciones acabó llamándose `to_out`, sin guion, porque lo reutiliza el repositorio de playlists: ver [[lesson-6]].)

---

## 3B · Conceptos enseñados — escrituras protegidas y capa de servicio

### 3B.1 `dependencies=[Depends(current_user)]` (decorador) frente a `user = Depends(current_user)` (parámetro)

| Forma | Qué hace | Cuándo |
|---|---|---|
| `@router.post(..., dependencies=[Depends(current_user)])` | **Exige** un token válido (si no, 401) pero **no te da el usuario** dentro de la función | Solo necesitas el *permiso*: `POST /artists`, `POST /songs` |
| `def f(user: models.User = Depends(current_user))` | Exige el token **y** te entrega el objeto `User` | Necesitas saber *quién* es: dueño de una playlist ([[lesson-6]]) |

En ambos casos `current_user` corre **antes** de tu función (FastAPI resuelve las dependencias primero y ejecuta el endpoint al final). Si `current_user` lanza `HTTPException(401)`, la función ni se ejecuta.

🔬 **Qué gana entre 401 y 422:** si falta el token **y** el cuerpo es inválido a la vez, la respuesta es **401**. Comprobado al redactar estas notas con `POST /songs` sin token y cuerpo `{"title": "", "duration_s": 0, ...}` → `401 {'error': {'code': 'unauthorized', 'message': 'Missing credentials'}}`; con `POST /artists` y `{"name": ""}` sin token → también 401. En clase no se probó este cruce (los tests de 422 siempre llevan token), pero es coherente con que `current_user` es una dependencia y se resuelve antes de levantar el error de validación.

### 3B.2 `status_code=201` y `response_model`

- `status_code=201` en el decorador fija el código de éxito de la **creación** (el contrato dice `201`, no `200`).
- `response_model=SongsOut` / `ArtistsOut` **filtra y serializa** la salida: lo que devuelve la función (un `dict` con `genre` como objeto SQLAlchemy y `artists` como lista de dicts) se valida contra el schema y sale como JSON. Es también lo que impide filtrar campos que no deben salir (en auth, `password_hash`).

### 3B.3 Quién valida qué: cuatro defensas, de fuera hacia dentro

| Capa | Qué comprueba | Respuesta | Ejemplo |
|---|---|---|---|
| **Schema Pydantic** (forma) | tipos, `Field(min_length, gt)`, `Literal`, `field_validator` | `422` (`validation_error`) | título vacío, rol `"dj"`, `duration_s == 0`, artista repetido |
| **Router** (HTTP) | auth, conflictos sencillos, traducción de excepciones | `401`, `409`, `404` | token ausente; nombre de artista repetido |
| **Service** (reglas de negocio) | cosas que requieren consultar la base | excepción propia → `404` en el router | género o artista inexistente |
| **Base de datos** (última defensa) | `UNIQUE`, PK compuesta, FK, `CHECK` | `IntegrityError` (→ 500 si nadie lo captura) | dos peticiones simultáneas con el mismo nombre de artista |

La idea: **cada error se detecta en la capa más barata y más cercana al cliente**, y las restricciones de la base quedan como red de seguridad, no como mecanismo normal.

### 3B.4 `@field_validator` (Pydantic v2): cómo sabe qué campo revisar

Pregunta del usuario (17:39): *"¿cómo `field_validator` sabe que debes checar `artists`? ¿Y cómo `classmethod` es necesario? Nunca había visto ese decorador. Supongo que lo que valida es precisamente el campo `artists` y la validación se hace in place dentro de esa solicitud."* Su suposición era **correcta**.

Respuesta, con pruebas ejecutadas en vivo:

- **Por el texto entre paréntesis.** `@field_validator("artists")` es una **etiqueta** que dice "esta función es para el campo llamado `artists`". Pydantic lee esas etiquetas **cuando Python define la clase** (al cargar el archivo), no cuando llega una petición. Después, al validar un cuerpo, cada vez que le toca el campo `artists` llama a la función.
- **Prueba:** con un nombre mal escrito, `@field_validator("artist")`, la clase **ni siquiera se pudo definir**: `PydanticUserError: Decorators defined with incorrect fields`. Pydantic comprueba que el nombre exista entre los campos.
- **Solo revisa lo que nombras.** Tu validador **no** revisa `title`, `duration_s` ni `genre_id`; esos se validan solo con su tipo y su `Field(...)`. Se pueden nombrar varios campos: `@field_validator("a", "b")`.
- **Cuándo corre y qué recibe.** Para el campo `artists` el orden es: (1) Pydantic valida el tipo y el `Field` (que sea lista y tenga al menos un elemento); (2) convierte cada diccionario en un objeto `SongArtistIn`; (3) **recién entonces** llama a tu validador, con `v` ya convertido. En la prueba, `v` llegó como `[Item(artist_id=1), Item(artist_id=2)]` (objetos, no diccionarios), incluso cuando el dato original era el texto `"2"`. Por eso puedes escribir `a.artist_id`. Si el tipo falla en el paso 1, **tu validador no se ejecuta**: el error de tipo sale primero.
- **`raise ValueError(...)`** es la forma de rechazar: Pydantic lo convierte en un error de validación y FastAPI lo responde como `422` (por el handler de `main.py`, con el formato `body.artists: Value error, …`).
- **`return v`** es obligatorio: lo que devuelves es el **valor final** del campo. Si lo olvidas, `artists` queda en `None`.
- **`len(ids) != len(set(ids))`** detecta repetidos: un `set` elimina duplicados, así que si el tamaño cambia, había repetidos.

```python
@field_validator("artists")      # ← para qué campo (se registra al definir la clase)
@classmethod                     # ← la función recibe la clase, porque aún no hay objeto
def no_duplicate_artists(cls, v):   # v = el valor ya validado de "artists"
    ...
    return v                     # ← lo que devuelves es el valor final del campo
```

### 3B.5 `@classmethod` — qué es y la corrección que hizo el tutor

Pregunta de seguimiento (17:43): *"si `field_validator` es una función de Pydantic y quiero asociar un método externo a la identidad de una clase, ¿tengo que definir ese decorador `classmethod`?"*

**Qué es.** `@classmethod` es un decorador **normal de Python**, no algo de Pydantic. Un método común recibe el objeto (`self`); un `@classmethod` recibe la **clase** (`cls`) y se puede llamar sin haber creado ningún objeto:

```python
class Fecha:
    def __init__(self, y): self.y = y
    @classmethod
    def desde_texto(cls, s):          # recibe la CLASE, no un objeto
        return cls(int(s[:4]))

Fecha.desde_texto("2026-10-23").y     # 2026: se llamó sobre la clase, sin crear un objeto antes
```

**Por qué encaja en un validador.** Mientras Pydantic valida los datos, **todavía no existe ningún `SongCreate`**: lo está construyendo, y tu función es uno de los pasos. Por eso la función recibe la clase (`cls`) y no un objeto (`self`). En la prueba, `cls` fue la clase y no había instancia.

**Quién hace qué** (esto corrigió la confusión del usuario):

| Pieza | Qué hace realmente |
|---|---|
| La función está **escrita dentro del cuerpo de la clase** | Es lo que hace que **pertenezca** a `SongCreate`. Pydantic recorre el cuerpo de la clase al construirla y recoge lo que encuentra marcado |
| `@field_validator("artists")` | **Asocia** la función con el campo `artists` (la etiqueta que Pydantic busca) |
| `@classmethod` | **No asocia nada.** Solo declara que el primer parámetro es la clase (`cls`) y no un objeto (`self`) |

Una función definida **fuera** de la clase no se vincula sola: se probó y una función externa con `field_validator` aplicado a mano no se ejecutó al crear el modelo.

**Corrección del tutor.** Antes se había dicho que `@classmethod` era "obligatorio"; no es del todo cierto. Probado:

- **Sin `@classmethod` y con `cls` como primer parámetro:** funciona (Pydantic lo envuelve por ti).
- **Sin `@classmethod` y con `self`:** `PydanticUserError: The @field_validator decorator cannot be applied to instance methods`.

Conclusión práctica: **no es obligatorio, pero ponlo siempre**, justo debajo de `@field_validator`. Es lo que muestra la documentación de Pydantic y lo que esperan editores y linters. En tu validador no usas `cls`, solo `v`, pero el parámetro tiene que estar.

### 3B.6 Alternativa: función externa con `Annotated` + `AfterValidator`

Si se quiere **reutilizar** la misma función en varios schemas, se puede enlazar sin clase y sin `cls`:

```python
from typing import Annotated
from pydantic import AfterValidator

def no_duplicates(v):                    # función normal, sin cls, recibe solo el valor
    ids = [a.artist_id for a in v]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate artist_id in artists")
    return v

class SongCreate(BaseModel):
    ...
    artists: Annotated[list[SongArtistIn], Field(min_length=1), AfterValidator(no_duplicates)]
```

Probado: funciona igual (mismo `ValueError` convertido en error de validación). Para un único caso, como este, basta `@field_validator`.

### 3B.7 Arquitectura por capas: router → service → repository

| Capa | Archivo | Sabe de… | NO sabe de… | Cómo señala un problema |
|---|---|---|---|---|
| Router | `routers/songs.py` | HTTP: status codes, `HTTPException`, `Depends`, auth | SQL, reglas | `raise HTTPException(...)` |
| Service | `services/songs.py` | reglas de negocio (¿existe el género?) | HTTP, FastAPI, SQL concreto | `raise RelatedNotFound(...)` (su propia excepción) |
| Repository | `repositories/songs.py` | SQL / SQLAlchemy | reglas, HTTP | devuelve `None` / `bool` / `set` |

Reglas del diseño (las que se verbalizaron en clase):

- **Cada capa hace una sola cosa**, y la dependencia apunta hacia abajo (router usa service, service usa repo; nunca al revés).
- **Los repositorios devuelven `None`** cuando no encuentran algo; **los routers deciden** el 404/409.
- **El service no importa FastAPI.** Eso lo hace reutilizable (un script, una tarea en segundo plano) y probable **sin HTTP** (`test_songs_service.py` no usa `TestClient`). Y se **vigila con un test** (`ast`): una regla de arquitectura que si se rompe, falla en CI.
- **¿Por qué una capa de servicio solo para esto?** Porque "¿existe el género?" y "¿existen todos los artistas?" **no son SQL ni HTTP**: son reglas. Si no se separan, acaban en el router (mezcladas con HTTP) o en el repositorio (mezcladas con SQL).
- Este patrón se repite en las playlists ([[lesson-6]]: `playlists_service`, con `SongNotFound` y `AlreadyInPlaylist`).

### 3B.8 Excepciones propias como señal entre capas

- Se define una excepción **vacía con docstring**: `class RelatedNotFound(Exception): """…"""`. Su valor no es el código, es el **nombre**: comunica el *qué pasó* en lenguaje de dominio.
- El service la lanza con un **mensaje** útil (`f"Artist(s) {missing} not found"`).
- El router la **captura con `except` específico** (`except songs_service.RelatedNotFound as e`) y la traduce: `raise HTTPException(status_code=404, detail=str(e))`.
- **Qué NO se captura** es parte del diseño: un `IntegrityError` u otro error inesperado no se atrapa y sube como 500 — correcto, porque sería un bug nuestro, no un error del cliente. Capturar `Exception` a ciegas escondería esos bugs.
- **`raise`, no `return`:** un `return HTTPException(...)` devolvería el objeto como si fuera datos (con 200 y un cuerpo raro). Es un error que ya mordió una vez en `depends.py`.

### 3B.9 `flush` frente a `commit`, atomicidad y `refresh`

| Operación | Qué hace | Transacción |
|---|---|---|
| `db.add(obj)` | prepara el objeto en la sesión; **no** toca la base | — |
| `db.flush()` | envía los `INSERT/UPDATE` pendientes a la base; **la base ya asigna ids** | sigue **abierta** |
| `db.commit()` | hace permanentes los cambios y cierra la transacción | cerrada |
| `db.refresh(obj)` | vuelve a leer el objeto desde la base (trae `id`, `created_at`…) | — |

El problema que resuelve `create_song`: necesitas el `song.id` para crear los vínculos `SongArtist`, pero **todavía no quieres confirmar** la canción. Solución:

```python
song = models.Song(...)
db.add(song)
db.flush()          # INSERT de la canción dentro de la transacción → song.id ya existe
db.add_all([models.SongArtist(song_id=song.id, ...) for ...])
db.commit()         # canción + vínculos, juntos
```

**Atomicidad = todo o nada.** Con un solo `commit` al final, si el vínculo con un artista falla, la transacción entera se descarta: no queda una **canción huérfana** sin artistas. Con dos `commit` (uno tras la canción) la canción ya estaría guardada cuando falle el vínculo. Los tests lo vigilan por dos lados: el repo (`test_failure_midway_leaves_no_orphan_song`) y la API (`test_failed_create_leaves_no_song_behind`).

Matiz sobre `db.py` 📝: `SessionLocal` se crea con `expire_on_commit=False`, es decir, tras el `commit` los objetos conservan sus valores en memoria en lugar de caducar y recargarse solos. Por eso `return song.id` después del `commit` funciona sin sorpresas. En `create_artist` el usuario añadió además `db.refresh(artist)` (el patrón de `create_user` en [[lesson-4]]) y devuelve `get_artist(...)`, que relee los datos del artista, `genres` incluido.

### 3B.10 `IN` en una sola consulta y la resta de conjuntos

`existing_artist_ids(db, ids)` hace **una** consulta (`WHERE artists.id IN (...)`) para N ids, en vez de N consultas (patrón anti-N+1 de la parte A). Con eso:

```python
ids = [a.artist_id for a in body.artists]                 # lo que pidió el cliente
existing = songs_repo.existing_artist_ids(db, ids)        # lo que existe
missing = sorted(set(ids) - existing)                     # lo que falta, ordenado
```

- `set(ids) - existing` es una **diferencia de conjuntos**: pedido menos existente = faltante.
- `sorted(...)` hace el mensaje **determinista** (`[77, 99]`) y testeable: un `set` no garantiza orden.
- Se reportan **todos** los faltantes de una vez (mejor para el cliente que fallar uno a uno).

### 3B.11 Validar todo *antes* de escribir

En `services/songs.py`, las dos comprobaciones (`genre_exists`, `existing_artist_ids`) van **antes** de `songs_repo.create_song`. Si algo falta, se lanza la excepción y **no se ha escrito nada**. Es una segunda línea de defensa de la atomicidad: lo que se puede comprobar de antemano no depende del rollback. Test: `test_nothing_is_written_when_validation_fails`.

### 3B.12 Reutilizar funciones existentes

- `create_artist` devuelve `get_artist(db, artist.id)`: el dict con `genres` (calculado) ya lo construye esa función.
- `service.create_song` devuelve `songs_repo.get_song(db, song_id)`: la misma que usa `GET /songs/{id}`. Por eso el test #8 puede exigir que `GET /songs/1` sea **igual** a lo que devolvió el POST.
- Regla práctica: si ya existe la función que construye la forma de salida, no se vuelve a escribir.

### 3B.13 Check-then-insert (409) y la restricción `UNIQUE` como red

`create_artist` en el router hace *comprobar primero, insertar después*:

```python
if artists_repo.get_by_name(db=db, name=body.name) is not None:
    raise HTTPException(status_code=409, ...)
return artists_repo.create_artist(...)
```

- Da un **error claro** en el caso normal (`409 conflict`).
- Pero entre la comprobación y el `INSERT` otra petición podría colarse: si dos peticiones con el mismo nombre llegan a la vez, ambas pasan el `get_by_name` y la segunda choca con `UNIQUE`. **La columna `UNIQUE` es la defensa real**; la comprobación previa es amabilidad.
- 📝 Hoy ese choque, si ocurriera, subiría como `IntegrityError` → 500 (no se capturó en esta lección). Mejora posible: capturar `IntegrityError` en `create_artist` y convertirlo en 409. Es la misma situación que `register` con el correo.

### 3B.14 Un stub duplicado oculta la implementación real

FastAPI registra **todas** las rutas y atiende la **primera** que coincide en método y ruta. Si el stub 501 y la implementación comparten `POST /songs`, gana el stub (el que está más arriba) y tu función real **nunca corre**. Síntoma en tests: todo falla con `501`. Receta: ante un 501 inesperado, buscar funciones duplicadas en el router. (Primera vez: `/me`; segunda: `POST /songs`.)

### 3B.15 Orden de ejecución: por qué los 422 pasaban con un stub

Pydantic valida el **cuerpo antes** de ejecutar tu función. Por eso, con el stub 501 activo, los 5 tests de cuerpo inválido seguían pasando (el 422 se produce antes de llegar al `raise HTTPException(501)`). Útil para razonar patrones de tests verdes/rojos: los tests que dependen solo de la validación pasan aunque la lógica no exista.

### 3B.16 Lista vacía = `200 []`; un listado vacío no es un error

- Un `GET` de colección con filtros sin resultados responde **`200` con `[]`**. `404` se reserva para **un recurso concreto** que no existe (`GET /songs/999`). Esto lo fija el contrato del README (*"GET lists with filters and no results return 200 []"*), y es lo que React necesita para pintar "no hay canciones".
- **Precedencia de `or`:** `songs is None or []` se evalúa como `(songs is None) or []`. Un `[]` suelto en una condición es siempre falsy; no significa "o lista vacía". Para eso sería `not songs`.
- **`raise HTTPException(status_code=200, ...)` es un antipatrón:** `raise` = camino de error (pasa por el handler, produce el sobre `{"error": …}`), `200` = éxito. Mezclarlos produce una respuesta contradictoria.
- 📝 Otros dos `if x is None: raise 404` del router de artistas (`list_artists`: `if artists is None`; `get_artist_songs`: `if songs is None`) están en la misma situación que el de `list_songs`: los repositorios devuelven listas, nunca `None`, así que esas ramas no se ejecutan jamás. No rompen nada; se pueden limpiar igual.

### 3B.17 Cómo se prueba cada capa sin pasar por la de arriba

La estrategia de esta lección: **tests por capa antes de conectar el router**, para tener *feedback* en cada paso:

| Capa | Archivo de test | Necesita HTTP | Herramientas |
|---|---|---|---|
| API completa | `test_write_api.py` | sí (`TestClient`, token real) | fixtures `client`, `base`, helper `auth_header` |
| Repositorio | `test_songs_write_repo.py` | no | fixture `db_factory` + `base` |
| Servicio | `test_songs_service.py` | no | `db_factory`, `SongCreate(**datos)`, `pytest.raises` |

Fixtures de `conftest.py` que se usan: `db_factory` (SQLite en **archivo** temporal con `expire_on_commit=False`; archivo y no `:memory:` porque el `TestClient` ejecuta los endpoints en otro hilo y cada conexión a `:memory:` sería una base distinta y vacía) y `client` (sobrescribe `get_db` con `app.dependency_overrides` para que la app use la base temporal). Cuando un test necesita **dos sesiones** (para verificar un commit), usa `with db_factory() as s1` y `with db_factory() as s2`.

### 3B.18 Tests de los tests: validación con implementación de referencia y mutaciones

El método que sigue el tutor con cada lección (útil también para ti):

1. Copiar el repo a un directorio temporal **sin** `.venv`, cachés ni `*.db`:
   ```bash
   d=$(mktemp -d); mkdir "$d/backend"
   tar --exclude=.venv --exclude=__pycache__ --exclude=.pytest_cache --exclude='*.db' -cf - . | tar -xf - -C "$d/backend"
   cd "$d/backend" && uv sync -q
   ```
2. Escribir la **solución de referencia** en la copia y comprobar que los tests pasan (`16 passed`).
3. **Mutar**: romper el código a propósito, de una en una (quitar una dependencia, un `commit`, un chequeo, invertir un `is not None`…) y comprobar que **algún test falla**. Si ninguno falla, el test es débil (o la mutación equivale al código correcto, ver 2B.4-C).
4. Restaurar y repetir.

Así se sabe que los tests **realmente vigilan** lo que dicen vigilar, y que "estar en verde" significa algo.

### 3B.19 Herramientas de comprobación y qué detecta cada una

| Comando | Qué detecta | Qué NO detecta |
|---|---|---|
| `uvx ruff check --select F,E9 app tests` | nombres no definidos, imports sin usar, errores de sintaxis | un `from app.security import current_user` cuando `current_user` no existe en ese módulo |
| `uv run python -c "import app.main"` | `ImportError`, módulos mal importados, errores al cargar la app | errores de lógica |
| `uv run pytest tests/test_x.py -q` | comportamiento | — |
| `uv run pytest -k "expr" -q` | selecciona por subcadena del nombre del test | cuidado con subcadenas demasiado genéricas |

---

## 4A. Errores cometidos y diagnóstico (parte A)

| # | Síntoma / traza | Causa | Arreglo | Lección |
|---|---|---|---|---|
| 1 | `ResponseValidationError: ... 'created_at' Field required` (previsto) | `GenreOut` exige `created_at` y la tabla `genres` no lo tenía | Añadir la columna al modelo y recrear `music.db` | Schema y modelo deben coincidir; `create_all` no altera tablas |
| 2 | `ModuleNotFoundError: No module named 'sqlalchemi'` | Typo en el import | `from sqlalchemy import select` | `ruff`/`import app.main` antes de `pytest` |
| 3 | `AttributeError: 'list' object has no attribute 'title'` | Se leyó `rows.title` en vez de `song.title`; `rows` es la lista de artistas | Cada campo sale de su fuente: `song`, `genre`, `rows` | Saber de qué variable viene cada dato |
| 4 | Género incorrecto (`db.get(models.Song, song_id)` pedía la canción otra vez) | Modelo equivocado | `db.get(models.Genre, song.genre_id)` | El FK de la canción da el id del género |
| 5 | `assert [] == [{'artist_id'...}]`, sin excepción | `.where(models.SongArtist == song_id)` → `WHERE false` | `.where(models.SongArtist.song_id == song_id)` | Error silencioso; mirar el `where`, `print(stmt)` |
| 6 | `assert 501 == 200` aunque el repositorio estaba bien | El router seguía con el stub 501 | Cablear el router (`Depends`, repo, 404) | Una función en dos capas: hay que arreglar ambas |
| 7 | `ImportError: cannot import name 'Session' from 'sqlalchemy'` → `2 errors during collection` | `from sqlalchemy import Session` | `from sqlalchemy.orm import Session` | Un error de import en un router rompe **toda** la suite |
| 8 | `NameError: name 'Depdends' is not defined` | Typo | `Depends` | Igual que 2 |
| 9 | `{'playlist_count': 2} != {'playlist_count': 1}` | `select(func.count())` sin `DISTINCT` | `func.count(distinct(PlaylistSong.playlist_id))` | El JOIN multiplica filas |
| 10 | Mismo fallo tras poner `.distinct()` | `.select_from(...).distinct()` genera `SELECT DISTINCT count(*)` (aplica al resultado, no dentro del conteo) | Poner `distinct` como argumento de `count` | Dos usos de "distinct" |
| 11 | `get_stats` declaraba `-> dict` y devolvía `None` | Tipo impreciso | `-> dict \| None` | Anotar `None` si puede devolverse |
| 12 | `NameError` en los 7 tests de lista (`artist_is`) | Typo, y además **tapaba** otros 3 errores | `artist_id` | Un error temprano oculta los siguientes |
| 13 | `song_ids` no definido en `_to_out` | Se definió `genre_ids` arriba y se usó otro nombre | `.in_([s.id for s in songs])` | — |
| 14 | `Artist` sin columna `artist_id` | La PK de `Artist` es `id` | `models.Artist.id == models.SongArtist.artist_id` | Nombres de columnas reales, no de FK |
| 15 | 5 tests rojos aun con el código "correcto" | `order_by(models.Song.title)` en lugar de `Song.id` | `order_by(models.Song.id)` | El orden forma parte del contrato (los tests lo exigían) |
| 16 | `ModuleNotFoundError: No module named 'fastappi'` (y `dastapi`) | Typos en los imports de `main.py` | `from fastapi.exceptions import ...`, `from fastapi.responses import ...` | Toda la app deja de importar |
| 17 | `raise HTTPException(status_code=200, ...)` para lista vacía (24 oct, al revisar) | Se usó una excepción para una respuesta buena y la condición `songs is None or []` nunca era verdadera | Borrar las dos líneas; devolver `200 []` | 404 vs lista vacía |
| 18 | Código muerto en `GET /artists` y `GET /artists/{id}/songs` (`if ... is None: raise 404`) | Los repositorios nunca devuelven `None` para listas | 📝 Pendiente de borrar | Idem |

**Errores del tutor en esta parte (corregidos en el diálogo):**

- Dijo que los schemas necesitaban `from_attributes`; no hace falta con `response_model`.
- Sugirió `-k genres`, que selecciona también `test_get_artist_with_genres`.
- Dijo "tres consultas por canción" para el N+1; la medición real fue 25 para 20 canciones (precisión en 2A.6).
- Se perdió la conexión con el ordenador del usuario a mitad de la sesión (el puente no responde si el chat no está abierto en la app de escritorio); se restableció al abrir la conversación desde la app de escritorio y pulsar "Link to this computer".

---

## 4B · Errores cometidos y diagnóstico

| # | Síntoma / traza | Causa | Arreglo | Lección |
|---|---|---|---|---|
| 1 | `test_stubs_answer_501`: `AssertionError: assert 401 == 501` | quedaba la línea `assert client.get("/me").status_code == 501` en `test_contract.py`; `/me` ya responde 401 sin token | borrar solo esa línea (la de `/playlists` se queda hasta [[lesson-6]]) | un test de "stubs pendientes" caduca cuando el stub se implementa; hay que podarlo al cerrar cada lección |
| 2 | `ImportError: cannot import name 'current_user' from 'app.security'` (`routers/artists.py`, línea 8) | importó `current_user` del módulo equivocado; vive en `depends.py` | `from app.depends import current_user` | `ruff --select F,E9` no lo ve; `import app.main` sí. Siempre las dos comprobaciones |
| 3 | `SongCreate(**dup)` no daba error al duplicar artista (en la prueba solo salía "sin title -> Field required") | pegó el esqueleto con `...` literal; el `@field_validator` **no estaba** en su archivo | añadir el método completo dentro de la clase, conservando los 4 campos | `...` en un esqueleto = "aquí van tus campos", no es código; copiar `...` borraría los campos |
| 4 | 6 tests de canciones fallan con `501`; patrón `.....FFFFFF.....` | **dos funciones `create_song` con el mismo `POST /songs`** (stub 501 arriba + la real al final); FastAPI usa la primera que coincide | borrar el stub (3 líneas) | misma causa que `/me` ([[lesson-4]]). Ante un 501 inesperado: buscar rutas duplicadas |
| 5 | (sin fallo visible) `if songs is None or []: raise HTTPException(404…)` en `list_songs` | `or []` siempre es falso → condición equivalente a `songs is None` → código muerto | borrar el `if` y el `raise`, `return songs` | un listado vacío es `200 []`, no un error; `or` tiene precedencia sobre la comparación |
| 6 | al "arreglarlo" a `if not songs:` el tutor vio 2 tests rojos (`test_list_songs_combined_filters`, `test_failed_create_leaves_no_song_behind`) | `not songs` convierte `[]` en 404 y contradice el contrato | no usarlo; borrar las dos líneas | los tests protegen el contrato frente a "arreglos" bienintencionados |
| 7 | (24-oct) `raise HTTPException(status_code=200, detail="No songs found")` | malinterpretó "no es 404" como "cámbialo por 200" | borrar el bloque, no cambiarle el código | `raise HTTPException` es para errores; con 200 saldría el sobre de error con status 200 |
| 8 | **Error del tutor:** dijo que `@classmethod` era "obligatorio" | no lo era: sin `@classmethod` y con `cls` funciona; con `self` da `PydanticUserError` | corrección explícita tras probarlo | verificar las afirmaciones en vez de explicar de memoria; ponerlo siempre por convención |
| 9 | **Falso negativo del tutor:** la mutación "faltantes sin ordenar" dio `5 passed` | la mutación (`[::-1]` sobre un `set`) coincidió con el orden de `sorted` por el orden interno de un `set` de enteros pequeños | repetir la mutación con otra forma (orden del cliente `[99, 77]`) → ahora sí falla `test_all_unknown_artists_are_reported_sorted` | un test que pasa bajo una mutación puede ser test débil **o** mutación mal elegida; hay que descartar la segunda |

Cosas que **no** fueron errores pero conviene recordar:

- El test #8 (`created == GET /songs/1`) falla si POST y GET devuelven formas distintas: protege contra "el POST devuelve algo que el GET no puede reproducir".
- 📝 En el repo final, `services/songs.py` mezcla estilos al llamar al repo (`existing_artist_ids(db=db, ids=ids)` con nombre; `get_song(db, song_id)` posicional). Funciona; solo conviene elegir un estilo.

---

## 5. Cómo se relaciona con el ritme

**Con el README (el contrato).** Esta lección implementa estas filas de la tabla de [[lesson-2]]:

| Fila del contrato | Dónde se hizo | Notas |
|---|---|---|
| `GET /genres` | 2A.3 | primer endpoint conectado de punta a punta |
| `GET /songs/{song_id}` | 2A.4 | canción con género y artistas (campos calculados) |
| `GET /artists/{artist_id}` | 2A.5 | 404 con el sobre de errores |
| `GET /artists` (`q`, `limit`, `offset`) | 2A.5 | orden por nombre; paginación |
| `GET /artists/{artist_id}/stats` | 2A.5 | `COUNT`, `COUNT DISTINCT`, géneros |
| `GET /songs` (`genre_id`, `artist_id`, `q`, `limit`, `offset`) | 2A.6 | filtros opcionales, `IN (subconsulta)`, N+1 evitado |
| `GET /artists/{artist_id}/songs` | 2A.7 | reutiliza casi todo lo anterior |
| Sobre de errores (404/422/401 con el mismo formato) | 2A.8 | `StarletteHTTPException` y `RequestValidationError` |
| `POST /artists` | 2B.2 | 201/401/422 y 409 (nombre repetido); la fila del README se amplió |
| `POST /songs` | 2B.4 | 201/401/404 (artista o género)/422; la fila se amplió con el 422 por artista repetido |

**Con el resto del proyecto.**

- Fija las **capas** (router → servicio → repositorio) que reaparecen en [[lesson-6]] y [[lesson-8]].
- Los datos sembrados en [[lesson-3]] (8 géneros, 13 artistas, 44 canciones) son los que consultan estos endpoints y los tests de integración.
- El formato de error unificado lo reutiliza todo lo posterior (playlists, auth, CORS).

**Con la entrevista.** Esta lección es la que más preguntas de "backend básico" cubre: JOINs y por qué un JOIN multiplica filas, paginación con orden estable, N+1 y cómo se arregla, filtros opcionales, 404 vs lista vacía, validación en varias capas, transacciones (`flush` vs `commit`), y por qué un servicio no debe importar FastAPI. Las preguntas concretas están en 6A y 6B.

## 6A. Preguntas de entrevista que salen de esta parte

1. **¿Dónde decides el 404: en el repositorio o en el router? ¿Por qué?** En el router. El 404 es un concepto HTTP; el repositorio no conoce HTTP y devuelve `None`. Así el repositorio se reutiliza (otros routers, scripts, tests) sin acoplarlo a FastAPI.
2. **¿Qué es el problema N+1 y cómo lo resuelves?** Una consulta para la lista y una más por elemento para sus relaciones (p. ej. 20 canciones → 25 consultas). Se resuelve cargando las relaciones de toda la página con una sola consulta `IN (...)` y agrupando en memoria (2 consultas). Con ORM también existen `selectinload`/`joinedload`.
3. **¿Por qué filtras por artista con `IN (subconsulta)` y no con `JOIN`?** Con `JOIN` la fila de la canción se duplica y el filtro descarta a los demás artistas de esa canción; con `IN` cada canción aparece una vez y se cargan *todos* sus artistas después.
4. **`COUNT(*)` vs `COUNT(DISTINCT col)`.** `COUNT(*)` cuenta filas del resultado del join; `COUNT(DISTINCT playlist_id)` cuenta playlists distintas. Si el JOIN multiplica filas, hay que contar la entidad con `DISTINCT`. `SELECT DISTINCT count(*)` no sirve: deduplica el resultado final.
5. **`execute` vs `scalars` vs `scalar` en SQLAlchemy.** `execute` → filas con varias columnas; `scalars` → la primera columna (o entidades) de cada fila; `scalar` → un único valor.
6. **¿Cómo haces estable una paginación?** `ORDER BY` determinista (una columna única o con desempate `id`), `limit` acotado (1–100) y `offset ≥ 0`. Mencionar que `offset` grande es costoso y que existe la paginación por keyset.
7. **¿Qué devuelve un listado sin resultados?** `200 []`, no 404: es una respuesta válida, y el cliente decide qué mostrar. El 404 es para un recurso concreto que no existe.
8. **¿Cómo unificas el formato de error en FastAPI?** Con `@app.exception_handler` para `StarletteHTTPException` (cubre también errores del framework: 404 de ruta, 405) y `RequestValidationError` (422), devolviendo `{"error": {"code", "message"}}`. Para los 500 inesperados, un tercer handler para `Exception`.
9. **¿Cómo pruebas endpoints que usan base de datos?** `TestClient` + base SQLite en archivo temporal + `app.dependency_overrides[get_db]` para inyectar la sesión de test; se siembra un catálogo pequeño con ids conocidos; después se verifica con mutaciones que los tests detectan los fallos.
10. **¿Por qué no `:memory:` con `TestClient`?** Porque ejecuta la app en otro hilo y cada conexión a `:memory:` crea una base distinta y vacía.
11. **Añadiste una columna al modelo y no aparece en la base. ¿Por qué?** `create_all` solo crea tablas que no existen. En producción se usan migraciones (Alembic); en desarrollo se recrea la base.
12. **¿`ilike` es eficiente para buscar texto?** No con `%texto%` (no usa índice normal); a escala se usa full-text search o trigramas. Para el ejercicio basta.
13. **¿Qué pasa si una función de repositorio hace una consulta por elemento dentro de un bucle y la reutilizas desde un listado?** Reaparece el N+1; se mide contando consultas con el evento `before_cursor_execute`. Se acepta con límites pequeños y se documenta la mejora.

## 6B · Preguntas de entrevista — escrituras protegidas y capa de servicio

1. **¿Qué diferencia hay entre `dependencies=[Depends(f)]` en el decorador y `x = Depends(f)` como parámetro?**
   Ambas ejecutan `f` antes del endpoint y cortan la petición si `f` lanza una excepción. La del decorador no entrega el valor a la función (sirve para exigir un permiso); la del parámetro sí (sirve para saber *quién* es el usuario).

2. **¿Para qué sirve una capa de servicio y por qué no debe importar FastAPI?**
   Contiene reglas de negocio ("¿existe el género?") que no son ni SQL ni HTTP. Si no importa FastAPI, no depende del framework: se puede reutilizar desde un script o un worker y se prueba sin `TestClient`. Señala problemas con excepciones propias y el router las traduce a códigos HTTP.

3. **¿Cómo garantizas que crear una canción y sus vínculos con artistas sea atómico?**
   `flush()` tras añadir la canción para obtener su `id` sin cerrar la transacción, se añaden los vínculos y **un único `commit()`** al final. Si algo falla antes, no se confirma nada y no queda una canción huérfana. Además, se valida todo antes de escribir.

4. **¿Diferencia entre `flush` y `commit` en SQLAlchemy?**
   `flush` manda las sentencias a la base dentro de la transacción abierta (asigna ids, pero otros no lo ven y se puede deshacer). `commit` las hace permanentes y cierra la transacción.

5. **¿Cómo compruebas que N artistas existen sin hacer N consultas?**
   Una consulta con `WHERE id IN (...)` que devuelve los ids existentes y una resta de conjuntos (`set(pedidos) - existentes`) para obtener los que faltan; se ordenan para que el mensaje sea estable.

6. **¿Cuándo 404, cuándo 409 y cuándo 422?**
   422: el cuerpo no cumple el schema (tipos, reglas de forma, duplicados dentro del propio cuerpo). 404: el cuerpo es válido pero hace referencia a algo que no existe (género o artista inexistente). 409: el recurso ya existe y chocaría con una restricción única (nombre de artista repetido).

7. **¿Cómo valida Pydantic v2 una regla que afecta a un campo concreto y qué papel tiene `@classmethod`?**
   Con `@field_validator("campo")` dentro de la clase: Pydantic registra la función al definir la clase y la ejecuta después de validar el tipo del campo, recibiendo el valor ya convertido. Se lanza `ValueError` para rechazar y se devuelve el valor. `@classmethod` indica que recibe la clase (`cls`), porque el objeto aún no existe; se recomienda siempre aunque con `cls` funcione sin él.

8. **¿Qué pasa si dos peticiones crean el mismo artista a la vez, si ya compruebas el nombre antes?**
   Ambas pueden pasar la comprobación; la segunda choca con la restricción `UNIQUE` de la base (`IntegrityError`). La restricción es la defensa real; la comprobación previa da un error amigable en el caso normal. Para cerrarlo del todo, capturar `IntegrityError` y devolver 409.

9. **¿Por qué `GET /songs` sin resultados devuelve `200 []` y no 404?**
   Una colección vacía es una respuesta válida; 404 se reserva para un recurso concreto inexistente. Además el cliente (React) pinta "no hay canciones" sin tratar el caso como error.

10. **Tienes un endpoint que devuelve 501 aunque ya lo implementaste. ¿Qué miras?**
    Si hay otra función registrada con el mismo método y ruta más arriba (el stub): FastAPI usa la primera que coincide.

11. **¿Cómo pruebas la lógica de negocio sin HTTP y cómo verificas que tus tests son buenos?**
    Llamando al servicio directamente con una sesión de base temporal y `pytest.raises` para las excepciones propias. Para los tests: implementación de referencia + mutaciones (rompo el código a propósito y compruebo que algún test falla); si ninguno falla, el test es débil.

12. **¿Qué ocurre si falta el token y el cuerpo es inválido a la vez?**
    Responde 401: la dependencia `current_user` se resuelve y corta antes de que se levante el error de validación del cuerpo (comprobado con `TestClient`).

## 7. Checklist / estado

Conseguido:

- [x] `GET /genres`, `GET /songs`, `GET /songs/{id}`, `GET /artists`, `GET /artists/{id}`, `GET /artists/{id}/songs`, `GET /artists/{id}/stats`
- [x] Filtros opcionales, `ilike`, paginación con orden estable
- [x] N+1 medido (25 → 2 consultas) y resuelto con `IN`
- [x] Sobre de errores unificado en `main.py` (`StarletteHTTPException` y `RequestValidationError`)
- [x] `POST /artists` y `POST /songs` protegidos con `current_user`
- [x] Capa `services/songs.py` con `RelatedNotFound`; `flush` vs `commit` entendido
- [x] `list_songs` devuelve `200 []` cuando no hay resultados
- [x] Suite en verde al cierre de cada mitad (46 passed y 92 passed, ambas con 1 skipped)

Pendiente (limpieza, tuya):

- [ ] Borrar las dos líneas comentadas del 404 en `list_songs` (`routers/songs.py`)
- [ ] Borrar las ramas inertes `if x is None` en `list_artists` y `get_artist_songs` (nunca se ejecutan) y corregir el `-k genres` de la docstring de `test_catalog_api.py`
- [ ] Marcar `Canciones y artistas` en el checklist del README y ampliar las filas de `POST /artists` (409) y `POST /songs` (422)
- [ ] Comprobar que el `.gitignore` existe y cubre `.venv/`, `__pycache__/` y `backend/data/*.db`
- [ ] Hacer el commit (incluye `pyproject.toml` y `uv.lock`)

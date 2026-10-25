---
tags: [fullstack-project-music, leccion, hecha]
leccion: 8
estado: hecha
---

# Lección 8 · pandas y NumPy: estadísticas por género y canciones parecidas

> **Objetivo:** añadir los dos endpoints de la **Fase 2** del README, `GET /stats/top-genres` (pandas) y `GET /songs/{song_id}/similar` (NumPy), con el mismo reparto de capas de siempre: SQL en `repositories/`, cálculo en `services/` como **funciones puras**, HTTP solo en `routers/`.
> **Duración prevista:** ~2 h, en 4 pasos, con 34 tests ya escritos por el tutor. Terminó con la suite en **153 passed, 1 skipped**.

Convenciones de estas notas: `📝` marca lo que no sale literalmente del diálogo de clase (ampliaciones, comprobaciones hechas al redactar, o cosas reconstruidas). Todo lo demás es lo que pasó en la lección.

---

## 0. Dónde encaja

- **No es uno de los 7 pasos de construcción** del README: es la **Fase 2**. Se hizo cuando ya estaba todo el backend base: entorno ([[lesson-1]]), contrato ([[lesson-2]]), modelos y semilla ([[lesson-3]]), autenticación ([[lesson-4]]), canciones y artistas ([[lesson-5]]) y playlists ([[lesson-6]]). El Dockerfile ([[lesson-7]]) sigue pendiente: el orden de recortes acordado era *Dockerfile → pandas/NumPy → playlists*, y hubo tiempo para pandas/NumPy.
- **Paso 0 previo (una línea de contexto):** antes de empezar había que añadir el middleware de CORS en `app/main.py` para poner en verde `tests/test_cors.py`. Eso se explica en [[lesson-9]]; aquí solo importa que la suite quedó en **119 passed, 1 skipped** antes de los tests nuevos.
- **Lo que viene después:** React ([[lesson-9]]). El `GET /songs` y estos dos endpoints son lo que el frontend consumirá.

### Los 4 pasos de la lección

| Paso | Qué | Archivo(s) | Tests | Tiempo previsto | "Verde" confirmado (hora) |
|---|---|---|---|---|---|
| 1 | pandas: `top_genres(rows, limit)`, función pura | `app/services/stats.py` | 9 (`test_stats_service.py`) | 30 min | 19:20 |
| 2 | pandas: consulta SQL + schema + router | `app/repositories/stats.py`, `app/routers/stats.py`, `app/schemas.py`, `app/main.py` | 7 (`test_stats_api.py`) | 25 min | 19:36 |
| 3 | NumPy: `feature_matrix` y `top_similar`, funciones puras | `app/services/similarity.py` | 10 (`test_similarity.py`) | 35 min | 20:08 |
| 4 | NumPy: endpoint `/songs/{id}/similar` | `app/repositories/songs.py`, `app/services/similarity.py`, `app/routers/songs.py`, `app/schemas.py` | 8 (`test_similar_api.py`) | 25 min | 20:43 |

Regla de tiempo de la lección: si te pasas de 30–40 min en un paso, se pide la solución completa (la regla general del entrenamiento es ~40 min).

### Qué hace cada endpoint (el contrato de la Fase 2)

| Endpoint | Qué hace |
|---|---|
| `GET /stats/top-genres?limit=5` | Por género: `song_count`, `playlist_count` (playlists **distintas**) y `avg_duration_s`. Orden: playlists ↓, canciones ↓, nombre ↑. **Incluye géneros sin canciones, con ceros.** `limit` de 1 a 50, por defecto 5. |
| `GET /songs/{song_id}/similar?limit=5` | Canciones parecidas por **similitud coseno**. Cada canción es un vector: género *one-hot* + artistas *multi-hot*. Excluye la propia canción y las de score 0. 404 si la canción no existe. `limit` de 1 a 50, por defecto 5. |

### Evolución de la suite durante la lección

| Momento | Resultado |
|---|---|
| Antes del Paso 0 (CORS) | 115 passed, 1 skipped (+ tests de CORS pendientes) |
| Con el middleware de CORS | **119 passed, 1 skipped** |
| Tests nuevos copiados pero `pandas`/`numpy` sin instalar | `Interrupted: 2 errors during collection` |
| Paso 1 | `test_stats_service.py` → 9 passed |
| Paso 2 | 9 + 7 = 16 passed; resto de la suite → 135 passed, 1 skipped |
| Paso 3 | `test_similarity.py` → 10 passed; suite sin el API de similar → 145 passed, 1 skipped |
| Paso 4 | `test_similar_api.py` → 8 passed; suite completa → **153 passed, 1 skipped** |

---

## 1. Qué se hizo (resumen)

1. Se instalaron `pandas` y `numpy` con `uv add` (cambian `pyproject.toml` y `uv.lock`, que hay que commitear).
2. **Paso 1.** Se escribió `top_genres` en `app/services/stats.py`: una función **pura** que recibe un `DataFrame` con una fila por (género, canción, playlist) y devuelve la lista de géneros con sus estadísticas. Trampas: un LEFT JOIN multiplica filas (hay que deduplicar antes de promediar), `count` ≠ `size` ≠ `nunique`, y los géneros sin canciones deben salir con ceros.
3. **Paso 2.** Se conectó con la base: `genre_rows(db)` en `repositories/stats.py` hace el triple LEFT JOIN (`outerjoin` de SQLAlchemy) y lo carga en un `DataFrame` con `pd.read_sql`; el router `GET /stats/top-genres` valida `limit` (1–50) y se registra en `main.py`.
4. **Paso 3.** Se escribió NumPy puro en `app/services/similarity.py`: `feature_matrix` (cada canción → vector de ceros y unos: columnas de géneros y después de artistas) y `top_similar` (similitud coseno de todas las canciones contra una, sin bucles).
5. **Paso 4.** Se conectó con la base: dos consultas nuevas en `repositories/songs.py`, la función orquestadora `similar_songs` en el servicio (traduce **id de canción → fila de la matriz**, redondea a 4 decimales) y el endpoint `GET /songs/{song_id}/similar` con 404 si no existe.
6. **Cierre.** Se completó el README (dos filas de contrato, dos filas de schemas, casilla marcada) y se hizo el commit.
7. **Por detrás:** el tutor escribió los 34 tests, los validó contra una implementación de referencia y los atacó con 20 *mutaciones* (rompiendo el código a propósito de 20 maneras) para comprobar que detectan los errores típicos. Eso hizo endurecer dos tests (orden estable y no mutar la matriz).

---

## 2. Paso a paso

### 2.0 Preparación: instalar, y por qué `pytest -q` se rompía

Los tests de la lección ya estaban en `backend/tests/`, y el tutor avisó: *hasta que implementes cada paso, `uv run pytest -q` mostrará errores de colección, así que usa siempre el archivo concreto.*

El usuario llegó a ese punto sin instalar las librerías y vio **"dos errores"** al ejecutar la suite completa:

```
ERROR tests/test_similarity.py     → ModuleNotFoundError: No module named 'numpy'
ERROR tests/test_stats_service.py  → ModuleNotFoundError: No module named 'pandas'
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
```

Diagnóstico: `test_similarity.py` y `test_stats_service.py` importan `numpy` / `pandas` en su **primera línea**, y todavía no estaban instalados. Pytest **no llega a ejecutar ningún test** porque la fase de *colección* (importar todos los archivos de test) falla: "Interrupted". No era un fallo del código del usuario (CORS estaba bien: `test_cors.py` daba 4 passed).

Instalación (una sola vez):

```bash
cd backend
uv add pandas numpy
```

Qué cambia (valores reales de `pyproject.toml` hoy):

```toml
dependencies = [
    ...
    "numpy>=2.5.4",
    "pandas>=3.1.0",
    ...
]
```

y se actualiza `uv.lock`. **Ambos archivos hay que commitearlos** (si no, quien clone el repo no tendrá las librerías).

Después de instalar, la suite completa seguía sin pasar por otro motivo: los tests nuevos fallan con `ModuleNotFoundError: app.services.stats` / `app.services.similarity` hasta escribir el código. Mientras tanto, para comprobar que el resto no se rompió:

```bash
uv run pytest -q --ignore=tests/test_stats_service.py --ignore=tests/test_stats_api.py \
  --ignore=tests/test_similarity.py --ignore=tests/test_similar_api.py
# esperado: 119 passed, 1 skipped
```

Y paso a paso, con el archivo concreto:

```bash
uv run pytest tests/test_stats_service.py -q      # 9 passed
```

Herramienta de comprobación que se usó en cada paso:

```bash
uvx ruff check --select F,E9 app tests
```

`F` = *pyflakes* (nombres no definidos, imports sin usar, variables sin usar) y `E9` = errores de sintaxis. Importante (se vio dos veces en esta lección): **ruff no detecta typos en atributos de un objeto** (`per_song.groupvy(...)`) **ni argumentos con nombre equivocados** (`top_similar(..., song_id=...)`); eso solo aparece al ejecutar.

---

### 2.1 Paso 1 · `top_genres` con pandas (función pura)

#### La entrada: una fila por (género, canción, playlist)

La función recibe un `DataFrame` que es el resultado de unir tres tablas con LEFT JOIN. Cada fila es una combinación (género, canción, playlist):

| genre_id | name | song_id | duration_s | playlist_id |
|---|---|---|---|---|
| 1 | Rock | 1 | 100 | 1 |
| 1 | Rock | 1 | 100 | 2 |
| 3 | Jazz | NaN | NaN | NaN |

- La canción 1 sale **dos veces** porque está en dos playlists (el JOIN **multiplica filas**).
- Jazz no tiene canciones, así que sus columnas llegan **vacías** (`NaN`).

De ahí salen las trampas que los tests vigilan.

#### El esqueleto que se dio (con huecos `...`)

```python
import pandas as pd


def top_genres(rows: pd.DataFrame, limit: int) -> list[dict]:
    # promediar filas repetidas deformaría la duración: ¿qué hay que deduplicar?
    # (ojo: dos géneros sin canciones tienen song_id vacío en ambos)
    per_song = rows.drop_duplicates([..., ...])
    stats = per_song.groupby(["genre_id", "name"], as_index=False).agg(
        song_count=("song_id", "..."),          # count (ignora NaN) o size (cuenta filas)
        avg_duration_s=("duration_s", "..."),
    )
    playlists = rows.groupby("genre_id", as_index=False).agg(
        playlist_count=("playlist_id", "..."),  # ¿count o nunique?
    )
    stats = stats.merge(playlists, on="genre_id", how="left")
    stats["avg_duration_s"] = ...               # sin canciones → 0.0; redondeado a 1 decimal
    stats = stats.sort_values([...], ascending=[...]).head(limit)
    return stats.astype({"song_count": int, "playlist_count": int}).to_dict("records")
```

Requisitos del orden del resultado: `playlist_count` descendente, luego `song_count` descendente, luego `name` ascendente.

Pistas que se dieron para los huecos:

- **`drop_duplicates`:** una canción puede repetirse por playlist, pero un género sin canciones tiene `song_id` vacío. Pensar qué **pareja de columnas** identifica una fila única.
- **`count` frente a `size`:** `count` ignora los vacíos y `size` cuenta todas las filas. Para Jazz, ¿cuántas canciones tiene?
- **`count` frente a `nunique`:** dos canciones del mismo género en la misma playlist cuentan **una vez**.
- **`ascending`:** la lista lleva un valor por cada columna de ordenación.

Dos reglas "no obvias" que se destacaron:

1. La función **no toca la base de datos**; por eso se prueba con un `DataFrame` hecho a mano, sin fixtures.
2. `limit` se aplica **después** de ordenar (los tests lo comprueban).

Y una nota de entrevista: esta agregación también se podría hacer en SQL con `GROUP BY`, y en producción sería lo habitual; pandas se justifica cuando los datos ya están en memoria o la transformación es incómoda en SQL. Si te lo preguntan, contesta eso.

#### La primera versión del usuario

El usuario llegó con esto y pidió ayuda en "la línea 17":

```python
def top_genres(rows: pd.DataFrame, limit: int) -> list[dict]:
    per_song = rows.drop_duplicates(subset=["song_id", "genre_id"])
    stats = per_song.groupvy(
        ["genre_id", "name"], as_index=False
    ).agg(
        song_count=("song_id", "count"),
        avg_duration_s=("duration_s", "mean")
    )
    playlists = rows.groupby("genre_id", as_index=False).agg(
        playlist_count=("playlist_id", "nunique")
    )
    stats = stats.merge(playlists, on="genre_id", how="left")
    stats["avg_duration_s"] = stats["avg_duration_s"].fillna(0).round(1)
    stats = stats.sort_values([...], ascending=[...]).head(limit)     # ← línea 17, sin rellenar
    return stats.astype({
        "song_count": int,
        "playlist_count": int,
        "avg_duration_s": float
    }).to_dict(orient="records")
```

**La línea 17 era el `sort_values`.** Se rellena traduciendo el orden pedido a columnas, en el mismo orden de prioridad:

| Prioridad | Criterio | Columna | `ascending` |
|---|---|---|---|
| 1.º | más playlists primero | `playlist_count` | `False` (de mayor a menor) |
| 2.º | desempate: más canciones | `song_count` | `False` |
| 3.º | desempate final: nombre | `name` | `True` (A→Z) |

```python
stats = stats.sort_values(
    ["playlist_count", "song_count", "name"],
    ascending=[False, False, True],
).head(limit)
```

Se explicó que pandas ordena primero por la primera columna y **solo mira la segunda cuando hay empate**. Por eso **Folk sale antes que Pop**: empatan en playlists y canciones, y `"Folk" < "Pop"`. Y `.head(limit)` va **después** de ordenar; si lo pones antes, recortas géneros "al azar" y luego ordenas lo que quedó.

Comentarios del tutor sobre el resto: `drop_duplicates` con `["song_id", "genre_id"]` está bien (el orden de las columnas da igual); `count`, `mean`, `nunique` y el `merge` están bien; incluir `"avg_duration_s": float` en el `astype` es **redundante, pero inofensivo**.

#### El error: `groupvy`

Al ejecutar `uv run pytest tests/test_stats_service.py -q` fallaron los **9 tests** con la misma traza:

```
app/services/stats.py:6: in top_genres
    stats = per_song.groupvy(
E   AttributeError: 'DataFrame' object has no attribute 'groupvy'. Did you mean: 'groupby'?
```

Diagnóstico: un **typo** (`groupvy` por `groupby`). Los 9 tests fallan igual porque todos llaman a `top_genres` y se rompe en la misma línea (cada test pasa un DataFrame distinto, pero el fallo es idéntico). Detalle de oficio: el propio Python sugiere la corrección (`Did you mean: 'groupby'?`); cuando un `AttributeError` muestre eso, casi siempre es un typo. Y **ruff no lo detecta**, porque `groupvy` es un método de un objeto y solo se descubre ejecutando.

#### Versión final (verde: 9 passed, ruff limpio)

Este es el código que hay hoy en `backend/app/services/stats.py`:

```python
import pandas as pd


def top_genres(rows: pd.DataFrame, limit: int) -> list[dict]:
    per_song = rows.drop_duplicates(subset=["song_id", "genre_id"])
    stats = per_song.groupby(
        ["genre_id", "name"], as_index=False
    ).agg(
        song_count=("song_id", "count"),
        avg_duration_s=("duration_s", "mean")
    )

    playlists = rows.groupby("genre_id", as_index=False).agg(
        playlist_count=("playlist_id", "nunique")
    )

    stats = stats.merge(playlists, on="genre_id", how="left")
    stats["avg_duration_s"] = stats["avg_duration_s"].fillna(0).round(1)
    stats = stats.sort_values(
        ["playlist_count", "song_count", "name"],
        ascending=[False, False, True]
    ).head(limit)

    return stats.astype({
        "song_count": int,
        "playlist_count": int,
        "avg_duration_s": float
    }).to_dict(orient="records")
```

#### Cómo se ve cada paso por dentro 📝

> 📝 Estas salidas **no salieron en clase**: las calculé al redactar las notas ejecutando exactamente tu función sobre los datos del test `ROWS` (pandas 3.0.5 / NumPy 2.5.3 en mi entorno; tu proyecto tiene `pandas>=3.1.0`, la lógica es la misma). Sirven para que veas qué hace cada línea.

Entrada (las columnas con `None` pasan a `float64`, por eso `song_id` aparece como `1.0`):

```
   genre_id   name  song_id  duration_s  playlist_id
0         1   Rock      1.0       100.0          1.0
1         1   Rock      1.0       100.0          2.0
2         1   Rock      2.0       200.0          1.0
3         2    Pop      3.0       300.0          1.0
4         4   Folk      4.0        60.0          1.0
5         3   Jazz      NaN         NaN          NaN
6         5  Blues      NaN         NaN          NaN
```

`drop_duplicates(subset=["song_id", "genre_id"])` quita la fila 1 (misma canción, otra playlist). Jazz y Blues **se quedan** porque su pareja `(NaN, 3)` y `(NaN, 5)` es distinta:

```
   genre_id   name  song_id  duration_s  playlist_id
0         1   Rock      1.0       100.0          1.0
2         1   Rock      2.0       200.0          1.0
3         2    Pop      3.0       300.0          1.0
4         4   Folk      4.0        60.0          1.0
5         3   Jazz      NaN         NaN          NaN
6         5  Blues      NaN         NaN          NaN
```

Si se deduplicara **solo por `song_id`**, pandas considera que todos los `NaN` son iguales entre sí, y **Blues desaparece** (se la come Jazz):

```
   genre_id  name  song_id  duration_s  playlist_id
0         1  Rock      1.0       100.0          1.0
2         1  Rock      2.0       200.0          1.0
3         2   Pop      3.0       300.0          1.0
4         4  Folk      4.0        60.0          1.0
5         3  Jazz      NaN         NaN          NaN        ← Blues no está
```

`groupby(["genre_id","name"]).agg(song_count=count, avg_duration_s=mean)` sobre `per_song`:

```
   genre_id   name  song_count  avg_duration_s
0         1   Rock           2           150.0
1         2    Pop           1           300.0
2         3   Jazz           0             NaN      ← count ignora NaN: 0 canciones
3         4   Folk           1            60.0
4         5  Blues           0             NaN
```

`playlist_count` con `nunique` sobre `rows` (¡el original, sin deduplicar!):

```
   genre_id  playlist_count
0         1               2      ← playlists 1 y 2 (la 1 aparece dos veces y cuenta una)
1         2               1
2         3               0
3         4               1
4         5               0
```

Tras `merge(..., how="left")`, `fillna(0).round(1)` y el `sort_values`:

```
   genre_id   name  song_count  avg_duration_s  playlist_count
0         1   Rock           2           150.0               2
3         4   Folk           1            60.0               1
1         2    Pop           1           300.0               1      ← empata con Folk; "Folk" < "Pop"
4         5  Blues           0             0.0               0
2         3   Jazz           0             0.0               0      ← "Blues" < "Jazz"
```

Y `.head(3).to_dict("records")` devuelve una lista de diccionarios con tipos de Python (justo lo que FastAPI serializará a JSON):

```python
[{'genre_id': 1, 'name': 'Rock', 'song_count': 2, 'avg_duration_s': 150.0, 'playlist_count': 2},
 {'genre_id': 4, 'name': 'Folk', 'song_count': 1, 'avg_duration_s': 60.0, 'playlist_count': 1},
 {'genre_id': 2, 'name': 'Pop',  'song_count': 1, 'avg_duration_s': 300.0, 'playlist_count': 1}]
```

#### Los 9 tests de `test_stats_service.py` y qué protege cada uno

El archivo trae su propio *helper* para construir DataFrames a mano:

```python
COLS = ["genre_id", "name", "song_id", "duration_s", "playlist_id"]

def frame(*rows):
    """Una fila por (género, canción, playlist). Lo que un LEFT JOIN no encuentra llega como None."""
    return pd.DataFrame(list(rows), columns=COLS)

# Rock(1): canción 1 (100 s, en dos playlists) y canción 2 (200 s)
# Pop(2): canción 3 (300 s) · Folk(4): canción 4 (60 s) · Jazz(3) y Blues(5): sin canciones
ROWS = [
    (1, "Rock", 1, 100, 1),
    (1, "Rock", 1, 100, 2),
    (1, "Rock", 2, 200, 1),
    (2, "Pop", 3, 300, 1),
    (4, "Folk", 4, 60, 1),
    (3, "Jazz", None, None, None),
    (5, "Blues", None, None, None),
]
```

| # | Test | Qué protege |
|---|---|---|
| 1 | `test_ranks_by_playlists_then_songs_then_name` | Orden completo: Rock, Folk, Pop, Blues, Jazz (con los ceros al final y desempate por nombre) |
| 2 | `test_avg_duration_counts_each_song_once` | Promedio **por canción**, no por fila: Rock da `150.0`, y promediar filas daría `133.3` |
| 3 | `test_avg_duration_is_rounded_to_one_decimal` | `(100+101+101)/3 = 100.67` → `100.7` |
| 4 | `test_playlist_counted_once_per_genre` | Dos canciones de Rock en la **misma** playlist cuentan una vez (`nunique`, no `count`) |
| 5 | `test_limit_applies_after_sorting` | `limit=2` → `["Rock", "Folk"]` (ordenar y luego recortar) |
| 6 | `test_only_genres_without_songs` | Solo géneros vacíos (columnas enteras de `None`, dtype `object`) no deben romper: salen Blues y Jazz con ceros |
| 7 | `test_empty_frame_returns_empty_list` | Un DataFrame vacío → `[]` |
| 8 | `test_returns_plain_python_types` | `int` y `float` de Python, no `numpy.int64`/`numpy.float64` |
| 9 | `test_does_not_modify_the_input_frame` | La función no muta el DataFrame de entrada (`pd.testing.assert_frame_equal` contra una copia) |

Comando y resultado esperados:

```bash
uvx ruff check --select F,E9 app tests      # All checks passed!
uv run pytest tests/test_stats_service.py -q   # 9 passed
```

---

### 2.2 Paso 2 · Consulta SQL y endpoint de `top-genres`

Hay que conectar la función pura con la base: una consulta que genere el `DataFrame`, un schema de respuesta y la ruta. **Cuatro piezas (A–D):**

**A. `app/schemas.py`** (al final):

```python
class GenreStats(BaseModel):
    genre_id: int
    name: str
    song_count: int
    playlist_count: int
    avg_duration_s: float
```

> Nota de nombres: el tutor, en su implementación de referencia, lo había llamado `GenreStat`; el README del proyecto lo llama `GenreStats`, y el usuario usó **`GenreStats`**. Es lo correcto (coincide con la tabla de schemas del README).

**B. `app/repositories/stats.py`** (nuevo). Tiene que devolver **exactamente** las columnas que espera `top_genres`: `genre_id, name, song_id, duration_s, playlist_id`. El esqueleto traía los `...` en las condiciones del JOIN:

```python
def genre_rows(db: Session) -> pd.DataFrame:
    stmt = (
        select(
            models.Genre.id.label("genre_id"),
            models.Genre.name,
            models.Song.id.label("song_id"),
            models.Song.duration_s,
            models.PlaylistSong.playlist_id,
        )
        .select_from(models.Genre)
        .outerjoin(models.Song, models.Song.genre_id == ...)
        .outerjoin(models.PlaylistSong, models.PlaylistSong.song_id == ...)
    )
    return pd.read_sql(stmt, db.connection())
```

**C. `app/routers/stats.py`** (nuevo), con los huecos de `Query(..., ge=..., le=...)` y de la llamada al servicio. "`limit` por defecto es 5 y va de 1 a 50."

**D. `app/main.py`:** importar `stats` en la línea `from app.routers import ...` y añadir `app.include_router(stats.router)`.

#### Versión final del usuario (verde: 16 passed entre los dos archivos de stats, ruff limpio, 135 passed del resto)

`app/repositories/stats.py`:

```python
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def genre_rows(db: Session) -> pd.DataFrame:
    stmt = (
        select(
            models.Genre.id.label("genre_id"),
            models.Genre.name,
            models.Song.id.label("song_id"),
            models.Song.duration_s,
            models.PlaylistSong.playlist_id,
        )
        .select_from(models.Genre)
        .outerjoin(models.Song, models.Song.genre_id == models.Genre.id)
        .outerjoin(models.PlaylistSong, models.PlaylistSong.song_id == models.Song.id)
    )
    return pd.read_sql(stmt, db.connection())
```

`app/routers/stats.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import stats as stats_repo
from app.schemas import GenreStats
from app.services import stats as stats_service


router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/top-genres", response_model=list[GenreStats])
def top_genres(limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    rows = stats_repo.genre_rows(db)
    return stats_service.top_genres(rows, limit)
```

`app/main.py` (hoy; el usuario lo refactorizó con un bucle, ver sección 6):

```python
from app.routers import artists, auth, genres, playlists, songs, users, stats
...
router_list = [artists, auth, genres, playlists, songs, users, stats]
for r in router_list:
    app.include_router(r.router)
```

Comprobación que se pidió:

```bash
uvx ruff check --select F,E9 app tests
uv run python -c "import app.main"          # detecta errores de import sin levantar el servidor
uv run pytest tests/test_stats_api.py -q    # 7 passed
```

#### Pregunta lateral del usuario: "¿por qué se usa `outerjoin` en `genre_rows`?"

Respuesta de clase: `join` normal (INNER) solo conserva las filas que tienen pareja en la otra tabla. `outerjoin` (un **LEFT JOIN**) conserva **todas las filas de la tabla de la izquierda**, tengan pareja o no, y rellena con `NULL` lo que no encuentra.

Con estos datos:

| genres | songs | playlist_songs |
|---|---|---|
| Rock, Jazz | S1 (Rock) | S1 en la playlist 1 |

**Con `join`** (inner) desaparece Jazz, porque no tiene ninguna canción:

| name | song_id | playlist_id |
|---|---|---|
| Rock | 1 | 1 |

**Con `outerjoin`** Jazz se queda, con vacíos:

| name | song_id | playlist_id |
|---|---|---|
| Rock | 1 | 1 |
| Jazz | NULL | NULL |

Y eso es lo que queremos: el contrato dice que los géneros sin canciones **aparecen con ceros**. Lo mismo vale para el **segundo** `outerjoin`: una canción que no está en ninguna playlist no debe desaparecer, porque sigue contando en `song_count`. Con `join` normal el endpoint devolvería **menos géneros de los que existen, sin dar ningún error**; `test_top_genres_ranking` lo detecta porque espera Blues, Jazz, Ska y Soul con ceros.

**Regla práctica:** si quieres "todos los X, tengan o no Y", usa `outerjoin` **desde X**.

📝 Comprobación al redactar: con los datos del test de la API (7 géneros, 4 canciones, 2 playlists), el triple LEFT JOIN produce estas 9 filas (lo que recibe pandas) y un INNER JOIN dejaría solo `Rock, Pop, Folk`:

```
(1, 'Rock',  1, 100,  1)
(1, 'Rock',  1, 100,  2)      ← la canción 1 está en dos playlists: fila repetida
(1, 'Rock',  2, 200,  1)
(2, 'Pop',   3, 300,  1)
(3, 'Jazz',  None, None, None)
(4, 'Folk',  4, 60,   1)
(5, 'Blues', None, None, None)
(6, 'Ska',   None, None, None)
(7, 'Soul',  None, None, None)
```

#### Otros detalles que se explicaron del repositorio

- **`select_from(models.Genre)`:** indica **desde qué tabla parte** la unión. Sin él, SQLAlchemy intentaría deducirlo y podría empezar por otra.
- **`.label("genre_id")` y `.label("song_id")`:** `Genre.id` y `Song.id` se llaman ambas `id`; el `DataFrame` necesita nombres de columna distintos y exactamente los que espera `top_genres`. 📝 (razonamiento de por qué hace falta; en clase solo se pidió "devolver exactamente esas columnas").
- **`pd.read_sql(stmt, db.connection())`:** carga el resultado de la consulta directamente en un `DataFrame`. 📝 Se le pasa `db.connection()` (la conexión que la sesión ya está usando) y no la `Session`, porque `read_sql` necesita algo que ejecute SQL; así la consulta corre en la misma base y transacción que el resto de la petición (y en los tests, en la base temporal que inyecta `dependency_overrides`).
- **Reparto de capas:** el repositorio **solo trae filas**, el servicio **decide cómo agregarlas** y el router **solo traduce HTTP** (mismo reparto que en las lecciones anteriores; ver [[lesson-5]]).
- **`Query(5, ge=1, le=50)`:** `limit` por defecto 5; fuera de 1–50 devuelve **422** con el sobre de error del proyecto (`{"error": {"code": "validation_error", ...}}`).

#### Los 7 tests de `test_stats_api.py`

Fixture `catalog` (siembra una base temporal con la fábrica `db_factory`; el `client` ya viene de `conftest.py` con `dependency_overrides`): 7 géneros (Rock, Pop, Jazz, Folk, Blues, Ska, Soul), 4 canciones (S1 100 s y S2 200 s en Rock, S3 300 s en Pop, S4 60 s en Folk), 2 playlists (P1 con las 4 canciones, P2 con la S1).

| Test (o grupo) | Qué comprueba |
|---|---|
| `test_top_genres_ranking` | JSON exacto con `limit=10`: Rock (2 canciones, 2 playlists, 150.0), Folk (1,1,60.0), Pop (1,1,300.0), luego Blues, Jazz, Ska, Soul con ceros |
| `test_top_genres_limit` | `limit=2` → `["Rock", "Folk"]` |
| `test_top_genres_default_limit_is_5` | Sin `limit` → 5 resultados, el último es `"Jazz"` |
| `test_top_genres_limit_out_of_range_is_422` (parametrizado con `0, 51, -1` → **3 tests**) | `422` y `error.code == "validation_error"` |
| `test_top_genres_empty_database_is_200_empty_list` | Base vacía → `200` y `[]` |

(5 funciones, 3 casos de parametrización → **7 tests** en total.)

Resultado confirmado: `16 passed` entre `test_stats_service.py` y `test_stats_api.py`; ruff limpio; `import-ok`; el resto de la suite (ignorando los tests de similar) en `135 passed, 1 skipped`.

#### Equivalente en SQL puro 📝

La nota de entrevista del Paso 1 decía que en producción esto sería un `GROUP BY`. Comprobé en SQLite con los mismos datos del test que esta consulta da **el mismo resultado**. Observa que tiene **la misma estructura que tu pandas**: dos agregaciones separadas y un LEFT JOIN (dos `groupby` + `merge` = dos CTE + LEFT JOIN). Si en cambio se hiciera un único `GROUP BY` sobre el JOIN triple, `AVG(duration_s)` promediaría filas repetidas (Rock saldría 133.33, el mismo error de los tests).

```sql
WITH per_song AS (
  SELECT genre_id, COUNT(*) AS song_count, AVG(duration_s) AS avg_duration_s
  FROM songs GROUP BY genre_id
), per_playlist AS (
  SELECT s.genre_id, COUNT(DISTINCT ps.playlist_id) AS playlist_count
  FROM songs s JOIN playlist_songs ps ON ps.song_id = s.id
  GROUP BY s.genre_id
)
SELECT g.id AS genre_id, g.name,
       COALESCE(a.song_count, 0)                AS song_count,
       COALESCE(p.playlist_count, 0)            AS playlist_count,
       ROUND(COALESCE(a.avg_duration_s, 0), 1)  AS avg_duration_s
FROM genres g
LEFT JOIN per_song     a ON a.genre_id = g.id
LEFT JOIN per_playlist p ON p.genre_id = g.id
ORDER BY playlist_count DESC, song_count DESC, g.name ASC
LIMIT 5;
```

Resultado con los datos del test: `Rock 2/2/150.0`, `Folk 1/1/60.0`, `Pop 1/1/300.0`, `Blues 0/0/0.0`, `Jazz 0/0/0.0`.

---

### 2.3 Paso 3 · NumPy puro: `feature_matrix` y `top_similar`

Archivo nuevo: `app/services/similarity.py`, con dos funciones que **no tocan la base de datos** (se prueban solo con arrays).

#### La idea

Cada canción se convierte en un **vector de ceros y unos**: una columna por género y una columna por artista. Dos canciones se parecen si sus vectores **apuntan en la misma dirección**, y eso lo mide la **similitud coseno**:

```
coseno(a, b) = (a · b) / (|a| · |b|)
```

`1` significa "mismos rasgos" y `0` "nada en común". Como los vectores son de ceros y unos, equivale a:

```
compartidos / √(rasgos_a · rasgos_b)
```

Ejemplo: S2 (Rock, Ana) y S1 (Rock, Ana, Beto) comparten 2 rasgos; S2 tiene 2 y S1 tiene 3 → `2/√(2·3) = 2/√6 = 0,8165`.

La gracia de NumPy es **no usar bucles**: se calcula la similitud de una canción contra todas a la vez.

#### El esqueleto que se dio

```python
import numpy as np


def feature_matrix(songs: list[tuple[int, int]], links: list[tuple[int, int]]) -> np.ndarray:
    """songs: (song_id, genre_id), en el orden de las filas. links: (song_id, artist_id)."""
    genre_ids = sorted({g for _, g in songs})
    artist_ids = sorted({a for _, a in links})
    g_col = {g: j for j, g in enumerate(genre_ids)}
    a_col = {a: ... + j for j, a in enumerate(artist_ids)}    # los artistas van DESPUÉS de los géneros
    row_of = {song_id: i for i, (song_id, _) in enumerate(songs)}

    m = np.zeros((len(songs), ... + ...))
    m[np.arange(len(songs)), [g_col[g] for _, g in songs]] = 1.0           # un 1 por canción: su género
    m[[row_of[s] for s, _ in links], [... for _, a in links]] = 1.0        # un 1 por cada (canción, artista)
    return m


def top_similar(matrix: np.ndarray, target: int, limit: int) -> list[tuple[int, float]]:
    dots = matrix @ matrix[target]                  # producto punto de TODAS las filas con la objetivo
    norms = np.linalg.norm(matrix, axis=1)
    denom = norms * norms[target]
    scores = np.divide(dots, denom, out=np.zeros_like(dots), where=...)    # solo donde se puede dividir
    order = np.argsort(..., kind="stable")          # de mayor a menor score
    ranked = [(int(i), float(scores[i])) for i in order if i != target and scores[i] > 0]
    return ranked[:limit]
```

Los huecos explicados:

- **`a_col`:** el desplazamiento es el número de géneros, `len(genre_ids)`; el mismo valor aparece en el tamaño de la matriz.
- **El segundo índice** de la segunda asignación: la columna de cada artista, `a_col[a]`.
- **`where=`:** dónde es válido dividir.
- **`argsort`:** ordena de menor a mayor, así que hay que darle los scores **con el signo cambiado**.

#### Las trampas que vigilan los tests (avisadas de antemano)

- **`np.divide` con `where=` y `out=`.** Un vector de ceros daría `0/0 = NaN` y un `RuntimeWarning`. El test convierte cualquier warning en error.
- **`kind="stable"`.** Sin él, los empates pueden salir en cualquier orden. El test usa 40 filas idénticas, porque con pocas el desorden no se nota.
- **`int(i)` y `float(...)`.** NumPy devuelve `np.int64`, que no es un `int` de Python; más adelante FastAPI/Pydantic fallarían al serializarlo.
- **No modificar la matriz.** Nada de `matrix /= ...`: el test usa una matriz de solo lectura.

#### La versión del usuario: "explícame este script"

El usuario pegó su primera versión y pidió que se la explicaran. Tenía **cuatro errores**, que se marcaron al final de la explicación:

```python
import numpy as numpy                                  # ← error 1


def feature_matrix(
    songs: list[tuple[int, int]],
    links: list[tuple[int, int]]
    ) -> np.ndarray:
    """songs: (song_id, genre_id), en el orden de las filas. links: (song_id, artist_id)."""
    genre_ids = sorted({g for _, g in songs})
    artist_ids = sorted(a for _, a in links)            # ← error 2 (faltan las llaves { })
    g_col = {g: j for j, g in enumerate(genre_ids)}
    a_col = {a: len(g_col) + j for a, j in enumerate(artist_ids)}   # ← error 3 (enumerate al revés)
    row_of = {song_id: i for i, (song_id, _) in enumerate(songs)}

    m = np.zeros((len(songs), len(g_col) + len(a_col)))
    m[np.arange(len(songs)), [g_col[g] for _, g in songs]] = 1.0
    m[[row_of[s] for s, _ in links], [a_col[a] for _, a in links]] = 1.0
    return m


def top_similar(matrix: np.ndarray, target: int, limit: int) -> list[tuple[int, float]]:
    dots = matrix @ matrix[target]
    norms = np.linalg.norm(matrix, axis=1)
    denom = norms * norms[target]
    scores = np.divide(dots, denom, out=np.zeros_like(dots), where=denom!=0)
    order = np.argsort(scores, kind="stable")           # ← error 4 (falta el signo menos)
    ranked = [(int(i), float(scores[i])) for i in order if i != target and scores[i] > 0]
    return ranked[:limit]
```

**Los cuatro errores:**

1. **`import numpy as numpy`** debe ser `import numpy as np`. Todo el código usa `np`, así que fallaría con `NameError`. **Ruff lo marca como `F821`** (nombre no definido).
2. **`artist_ids = sorted(a for _, a in links)`** le faltan las llaves. Sin el *conjunto*, el artista 7 aparece **dos veces** en la lista (una por cada canción en la que sale). Debe ser `sorted({a for _, a in links})`.
3. **`for a, j in enumerate(artist_ids)`** tiene el orden invertido. `enumerate` devuelve `(posición, valor)`, igual que en `g_col` (donde sí lo escribió bien). Debe ser `for j, a in enumerate(artist_ids)`. Tal como estaba, las claves del diccionario eran posiciones y no ids de artista, y `a_col[a]` daría `KeyError`.
4. **`np.argsort(scores, ...)`** ordena de menor a mayor, y se quieren las más parecidas primero. Debe ser `np.argsort(-scores, kind="stable")`.

Lo que sí estaba bien: `where=denom!=0` (las normas nunca son negativas, así que equivale a `denom > 0`).

#### Explicación línea a línea con el ejemplo del test

Canciones `[(1,10), (2,10), (3,20)]` (id, género) y vínculos `[(1,7), (1,8), (2,7), (3,9)]` (id, artista).

**`feature_matrix`:**

- **`genre_ids`** = géneros distintos y ordenados, `[10, 20]`. **`g_col`** dice en qué columna va cada uno: `{10: 0, 20: 1}`.
- **`artist_ids` y `a_col`** hacen lo mismo con los artistas, `{7: 2, 8: 3, 9: 4}`. Empiezan en `len(g_col)` porque sus columnas van **después** de las de géneros.
- **`row_of`** dice en qué fila va cada canción: `{1: 0, 2: 1, 3: 2}`.
- **`np.zeros((3, 5))`** crea la matriz vacía: 3 canciones por 5 columnas (2 géneros + 3 artistas).
- **La primera asignación** `m[filas, columnas] = 1.0` pone el género. Los dos índices se emparejan **posición a posición**, como coordenadas, no como combinaciones: `(0,0)`, `(1,0)`, `(2,1)`. (Esto se llama *fancy indexing* con listas.)
- **La segunda asignación** hace lo mismo con los artistas: `(0,2)`, `(0,3)`, `(1,2)`, `(2,4)`.

Resultado:

```
[[1, 0, 1, 1, 0],    canción 1: género 10, artistas 7 y 8
 [1, 0, 1, 0, 0],    canción 2: género 10, artista 7
 [0, 1, 0, 0, 1]]    canción 3: género 20, artista 9
```

📝 Salida real al ejecutarlo (dtype `float64`, forma `(3, 5)`):

```
filas de la 1ª asignación: [0, 1, 2]   columnas: [0, 0, 1]
filas de la 2ª asignación: [0, 0, 1, 2]  columnas: [2, 3, 2, 4]
[[1. 0. 1. 1. 0.]
 [1. 0. 1. 0. 0.]
 [0. 1. 0. 0. 1.]]
```

**`top_similar`** con `target = 1` (la canción 2, fila 1):

- **`dots = matrix @ matrix[target]`** calcula el producto punto de **todas** las filas con la objetivo, de una vez y sin bucle: `[2, 2, 0]`.
- **`norms`** es el tamaño de cada vector y **`denom`** el producto de cada tamaño por el de la objetivo.
- **`scores = np.divide(...)`** divide `dots / denom`, pero solo donde `denom` no es cero; donde sí lo es, deja `0.0` (el `out=np.zeros_like(dots)`). Así un vector vacío no da `NaN` ni warning. Resultado: `[0.8165, 1.0, 0.0]`.
- **`order = argsort`** ordena los **índices** por score.
- **`ranked`** descarta la propia canción (que siempre sale con 1.0) y las de score 0, y convierte a `int` y `float` de Python.
- **`[:limit]`** se queda con las primeras.

📝 Valores reales de ese ejemplo:

```
dots   = [2. 2. 0.]
norms  = [1.7321 1.4142 1.4142]
denom  = [2.4495 2.     2.    ]
scores = [0.8165 1.     0.    ]
np.argsort(scores)   → [2, 0, 1]   ← de menor a mayor: la peor primero (el error 4)
np.argsort(-scores)  → [1, 0, 2]   ← la más parecida primero (la propia canción, que se descarta luego)
```

#### Versión final (verde: 10 passed, ruff limpio, 145 passed del resto)

Las dos funciones puras de `app/services/similarity.py` tal como están hoy:

```python
import numpy as np


def feature_matrix(
    songs: list[tuple[int, int]],
    links: list[tuple[int, int]]
    ) -> np.ndarray:
    """songs: (song_id, genre_id), en el orden de las filas. links: (song_id, artist_id)."""
    genre_ids = sorted({g for _, g in songs})
    artist_ids = sorted({a for _, a in links})
    g_col = {g: j for j, g in enumerate(genre_ids)}
    a_col = {a: len(g_col) + j for j, a in enumerate(artist_ids)}
    row_of = {song_id: i for i, (song_id, _) in enumerate(songs)}

    m = np.zeros((len(songs), len(g_col) + len(a_col)))
    m[np.arange(len(songs)), [g_col[g] for _, g in songs]] = 1.0
    m[[row_of[s] for s, _ in links], [a_col[a] for _, a in links]] = 1.0
    return m


def top_similar(
    matrix: np.ndarray,
    target: int,
    limit: int
) -> list[tuple[int, float]]:
    dots = matrix @ matrix[target]
    norms = np.linalg.norm(matrix, axis=1)
    denom = norms * norms[target]
    scores = np.divide(dots, denom, out=np.zeros_like(dots), where=denom!=0)
    order = np.argsort(-scores, kind="stable")
    ranked = [(int(i), float(scores[i])) for i in order if i != target and scores[i] > 0]
    return ranked[:limit]
```

#### Los 10 tests de `test_similarity.py`

Datos que usan: una matriz `M` de 5 filas con casos de borde y `setflags(write=False)`:

```python
M = np.array([
    [1, 1, 0],      # 0  (objetivo)
    [1, 1, 0],      # 1  idéntica
    [1, 0, 0],      # 2  comparte una de dos
    [0, 0, 1],      # 3  nada en común
    [0, 0, 0],      # 4  vector cero
], dtype=float)
M.setflags(write=False)       # si una función modifica la matriz en el sitio, falla con ValueError
```

| # | Test | Qué protege |
|---|---|---|
| 1 | `test_feature_matrix_layout` | Disposición exacta: géneros primero, luego artistas, ambos ordenados por id; `dtype == float64` |
| 2 | `test_feature_matrix_empty` | Sin canciones → forma `(0, 0)` |
| 3 | `test_feature_matrix_song_without_artists_keeps_its_genre` | Una canción sin artistas conserva su género: `[[1]]` |
| 4 | `test_scores_and_order` | Fila 1 con score `1.0`, fila 2 con `1/√2`; orden `[1, 2]` |
| 5 | `test_excludes_target_and_non_positive_scores` | La objetivo no aparece; si no hay nada en común → `[]` |
| 6 | `test_ties_keep_row_order` | 40 filas idénticas: todas empatan y salen **en orden de fila** (`argsort` estable) |
| 7 | `test_limit` | `limit=1` → `[1]`; `limit=100` no inventa filas (solo 2) |
| 8 | `test_zero_vectors_do_not_warn_or_produce_nan` | Con `warnings.simplefilter("error")`: ni el objetivo vector-cero ni un candidato vector-cero producen warning ni `NaN` |
| 9 | `test_returns_plain_python_numbers` | `type(i) is int` y `type(s) is float` |
| 10 | `test_does_not_modify_the_matrix` | Con una matriz de normas distintas de 1 (`[[3,4,0],[1,0,0],[0,0,2]]`) comprueba que no se normaliza en el sitio |

Comandos y resultado:

```bash
uvx ruff check --select F,E9 app tests          # All checks passed!
uv run pytest tests/test_similarity.py -q       # 10 passed
uv run pytest -q --ignore=tests/test_similar_api.py   # 145 passed, 1 skipped
```

---

### 2.4 Paso 4 · El endpoint `/songs/{song_id}/similar`

Conectar las funciones puras con la base de datos. **Cuatro piezas (A–D):**

**A. `app/schemas.py`** (al final):

```python
class SimilarSong(BaseModel):
    song_id: int
    title: str
    score: float
```

**B. `app/repositories/songs.py`:** dos consultas que alimentan a `feature_matrix`. Las canciones deben salir **ordenadas por id**, "porque el orden de las filas decide el desempate". Esqueleto:

```python
def list_song_rows(db: Session) -> list[tuple[int, str, int]]:
    stmt = select(models.Song.id, models.Song.title, models.Song....).order_by(models.Song....)
    return [tuple(r) for r in db.execute(stmt)]


def list_song_artist_links(db: Session) -> list[tuple[int, int]]:
    stmt = select(models.SongArtist.song_id, models.SongArtist....)
    return [tuple(r) for r in db.execute(stmt)]
```

(`tuple(r)` convierte cada `Row` de SQLAlchemy en una tupla normal, para que el servicio no dependa de SQLAlchemy.)

**C. `app/services/similarity.py`:** la función que orquesta (más los imports `Session` y `songs_repo`). Esqueleto con el hueco clave:

```python
def similar_songs(db: Session, song_id: int, limit: int) -> list[dict]:
    rows = songs_repo.list_song_rows(db)                  # (id, title, genre_id), por id
    links = songs_repo.list_song_artist_links(db)
    matrix = feature_matrix([(sid, gid) for sid, _, gid in rows], links)
    target = ...                                           # ¿en qué FILA de la matriz está song_id?
    return [
        {"song_id": rows[i][0], "title": rows[i][1], "score": round(score, 4)}
        for i, score in top_similar(matrix, ..., ...)
    ]
```

**D. `app/routers/songs.py`:** importar `SimilarSong`, importar `similarity_service` y escribir el endpoint (con el `status_code=...` y los argumentos del servicio como huecos).

Qué mirar (las tres indicaciones del tutor):

- **El `target`.** `top_similar` espera el **índice de la fila**, no el id de la canción. Son distintos: la canción con id 5 puede estar en la fila 4. Hay que buscar en `rows` la fila cuyo id coincida.
- **El 404 va en el router.** El servicio da por hecho que la canción existe; por eso se comprueba antes (`song_exists`/`get_song`).
- **El redondeo está en el servicio.** `top_similar` devuelve los números sin tocar y el formato de la respuesta se decide una capa más arriba.

Nota de entrevista del tutor: este diseño **reconstruye la matriz entera en cada petición**; está bien para un ejercicio. En producción se precalcularía (caché) o se usaría una base de vectores (pgvector, FAISS).

#### La versión del usuario y sus tres errores

```python
def similar_songs(db: Session, song_id: int, limit: int) -> list[dict]:
    rows = songs_repo.list_song_rows(db)
    links = songs_repo.list_song_artist_links(db)
    matrix = feature_matrix(
        [(sid, gid) for sid, _, gid in rows],
        links
    )
    target = song_id                                                          # ← error 1
    return [
        {"song_id": rows[i][0], "title": rows[i][1], "score": score}          # ← error 3 (sin round)
        for i, score in top_similar(matrix=matrix, song_id=target, limit=limit)   # ← error 2
    ]
```

1. **`target = song_id` mezcla dos cosas distintas** (el error importante). `top_similar` espera el **índice de fila**, y se le pasa el **id**. Coinciden solo por casualidad: en los tests los ids son 1 a 6 y las filas 0 a 5, así que la canción con id 2 está en la fila 1. Con ese código se pediría la similitud de la fila 2 (la canción 3) y la respuesta sería **de otra canción, sin ningún error**. Si los ids tuvieran huecos, fallaría con `IndexError`.
2. **El argumento se llama `target`, no `song_id`.** `top_similar(matrix=matrix, song_id=target, ...)` falla con `TypeError: unexpected keyword argument 'song_id'`. (Ruff no lo ve.)
3. **Falta el `round(score, 4)`.** Sin él, la respuesta trae `0.816496580927726` y los tests esperan `0.8165`.

La corrección: un diccionario `row_of` que traduce **id → fila**, el mismo patrón que ya usa `feature_matrix` por dentro:

```python
    row_of = {sid: i for i, (sid, _, _) in enumerate(rows)}      # id de canción → fila de la matriz
    target = row_of[song_id]
```

#### Versión final del usuario (verde: 8 passed, ruff limpio, 153 passed, 1 skipped)

`app/services/similarity.py` (la parte nueva; se añadieron los imports `from sqlalchemy.orm import Session` y `from app.repositories import songs as songs_repo` arriba):

```python
def similar_songs(db: Session, song_id: int, limit: int) -> list[dict]:
    rows = songs_repo.list_song_rows(db)
    links = songs_repo.list_song_artist_links(db)
    matrix = feature_matrix(
        [(sid, gid) for sid, _, gid in rows],
        links
    )
    row_of = {sid: i for i, (sid, _, _) in enumerate(rows)}
    target = row_of[song_id]
    return [
        {"song_id": rows[i][0], "title": rows[i][1], "score": round(score, 4)}
        for i, score in top_similar(matrix=matrix, target=target, limit=limit)
    ]
```

`app/repositories/songs.py` (estado actual):

```python
def list_song_rows(db: Session) -> list[tuple[int, str, int]]:
    stmt = select(models.Song.id, models.Song.title, models.Song.genre_id)
    return [tuple(r) for r in db.execute(stmt)]


def list_song_artist_links(db: Session) -> list[tuple[int, int]]:
    stmt = select(models.SongArtist.song_id, models.SongArtist.artist_id)
    return [tuple(r) for r in db.execute(stmt)]
```

`app/routers/songs.py` (estado actual):

```python
@router.get("/{song_id}/similar", response_model=list[SimilarSong])
def similar_song(song_id: int, limit:int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    if not songs_repo.get_song(db, song_id):
        raise HTTPException(status_code=404, detail=f"Song {song_id} not fount")
    return similarity_service.similar_songs(db, song_id, limit)
```

#### Los 8 tests de `test_similar_api.py`

Fixture `library` (3 géneros, 4 artistas, 6 canciones):

```
S1 Rock  [Ana main, Beto featured]      S4 Rock [Caro]
S2 Rock  [Ana]                          S5 Pop  [Caro]
S3 Pop   [Ana]                          S6 Jazz [Dina]   (aislada)
```

Por qué salen esos números (con `compartidos / √(rasgos_a · rasgos_b)`):

- **S2** (Rock, Ana = 2 rasgos) frente a **S1** (Rock, Ana, Beto = 3): comparten 2 → `2/√6 = 0.8165`. Frente a **S3** (Pop, Ana): comparten Ana → `1/√4 = 0.5`. Frente a **S4** (Rock, Caro): comparten Rock → `0.5`. S5 y S6: 0 (no aparecen). Orden: S1, luego S3 y S4 empatadas **por id** (orden de fila estable).
- **S1** (3 rasgos) frente a S2: `2/√6 = 0.8165`; frente a S3 y S4: `1/√6 = 0.4082`.
- **S5** (Pop, Caro): S3 comparte Pop (0.5), S4 comparte Caro (0.5) → `[3, 4]`.

| Test | Qué comprueba |
|---|---|
| `test_similar_ranks_by_shared_genre_and_artists` | `/songs/2/similar` → `[S1 0.8165, S3 0.5, S4 0.5]` |
| `test_similar_with_featured_artist` | `/songs/1/similar` → `[S2 0.8165, S3 0.4082, S4 0.4082]` (el artista *featured* también cuenta) |
| `test_similar_limit` | `limit=1` → solo `[S1 0.8165]` |
| `test_similar_excludes_itself_and_zero_scores` | `/songs/5/similar` → ids `[3, 4]` |
| `test_similar_isolated_song_is_200_empty_list` | `/songs/6/similar` (aislada) → `200` y `[]` (no es un error) |
| `test_similar_unknown_song_is_404` | `/songs/99/similar` → `404`, `error.code == "not_found"` y `"99"` en el mensaje |
| `test_similar_limit_out_of_range_is_422` (parametrizado `0, 51` → **2 tests**) | `422` |

(7 funciones, 1 con 2 casos → **8 tests**.)

#### Comprobación final de la lección

```bash
uvx ruff check --select F,E9 app tests          # All checks passed!
uv run python -c "import app.main"              # import-ok
uv run pytest tests/test_similar_api.py -q      # 8 passed
uv run pytest -q                                # 153 passed, 1 skipped
```

---

### 2.5 Cierre: README y commit

Con la suite en verde, se cerró el README (5 min):

1. **Tabla del contrato.** Sustituir la línea de "Fase 2" por dos filas dentro de la tabla de rutas:

```
| `GET /stats/top-genres` | no | `limit` (1–50, por defecto 5) | 200 `list[GenreStats]` | 422 |
| `GET /songs/{song_id}/similar` | no | `limit` (1–50, por defecto 5) | 200 `list[SimilarSong]` | 404, 422 |
```

2. **Tabla de schemas.** Añadir:

```
| `GenreStats` | `genre_id`, `name`, `song_count`, `playlist_count`, `avg_duration_s` |
| `SimilarSong` | `song_id`, `title`, `score` (coseno, 4 decimales) |
```

3. **Lista de pasos.** Cambiar a `- [x] pandas: /stats/top-genres · NumPy: /songs/{id}/similar` (y marcar también *Playlists* si faltaba).
4. **Commit** (lo hace el usuario). Recordatorio: incluir `pyproject.toml` y `uv.lock`, que cambiaron al instalar pandas y NumPy.

Estado actual del README (comprobado al redactar): las dos filas de contrato están (líneas 69–70), la casilla pandas/NumPy está marcada (línea 142) y las filas de schemas `GenreStats`/`SimilarSong` están, aunque **aparecen duplicadas** (líneas 94–97, dos veces cada una): ver pendientes en la sección 7.

---

### 2.6 Cómo se validaron los tests: implementación de referencia + mutaciones

Esto es trabajo del tutor, pero conviene entenderlo porque explica **por qué cada test existe**.

**Método.** Los 34 tests nuevos se probaron contra una **implementación de referencia** escrita en una copia temporal del proyecto (nunca en el repo del usuario): pasaron 34/34 y la suite completa dio **153 passed, 1 skipped**. Luego se hizo **test de mutaciones**: se rompe el código a propósito de una forma concreta y se comprueba que algún test falla (se dice que el test "mata" la mutación). Si todos los tests siguen pasando, la mutación "sobrevive" y hay un hueco en los tests.

Resultados de las 20 mutaciones (tests que fallaron / pasaron):

| Módulo | Mutación | Resultado |
|---|---|---|
| stats | Promediar filas (sin `drop_duplicates`) | 3 fallan → detectada |
| stats | `drop_duplicates` solo por `song_id` | 4 fallan → detectada |
| stats | `playlist_count` con `count` en vez de `nunique` | 3 fallan → detectada |
| stats | Sin normalizar dtypes a `float64` | **sobrevive** (equivalente, ver abajo) |
| stats | Sin `round(1)` | 1 falla → detectada |
| stats | Sin `fillna` | 3 fallan → detectada |
| stats | Nombre en orden descendente | 6 fallan → detectada |
| stats | Sin la guarda de DataFrame vacío | **sobrevive** (equivalente) |
| stats | `merge` con `how="inner"` | **sobrevive** (equivalente) |
| stats | `.head(limit)` antes de ordenar | 2 fallan → detectada |
| sim | Sin normalizar (solo producto punto) | 4 fallan → detectada |
| sim | División directa `dots / denom` (`NaN` y warnings) | 1 falla (+5 warnings) → detectada |
| sim | Incluir la propia canción | 9 fallan → detectada |
| sim | Incluir scores cero | 8 fallan → detectada |
| sim | Dejar `np.int64` sin convertir a `int` | 1 falla → detectada |
| sim | Ordenar ascendente | 5 fallan → detectada |
| sim | `argsort` **no estable** | **sobrevivió** al principio → test endurecido |
| sim | **Mutar la matriz** de entrada | **sobrevivió** al principio → test endurecido |
| sim | Columnas sin ordenar | 1 falla → detectada |
| sim | Scores sin redondear (en el servicio) | 3 fallan → detectada |

**Las dos que sobrevivían de verdad y cómo se arreglaron:**

- **Orden no estable.** Con 4 filas iguales, un orden "inestable" puede salir bien por casualidad. Se cambió el test de empates a **40 filas idénticas** (`np.ones((40, 2))`): todas empatan y deben salir en orden de fila. Con eso la mutación pasó a fallar (1 failed).
- **Mutar la matriz.** El test original comparaba `M` con una copia, pero con una matriz cuyas filas ya tenían norma 1 normalizar no la cambiaba. Se cambió a una matriz con **normas distintas de 1** y, además, `M.setflags(write=False)` en la matriz compartida: cualquier modificación in-situ lanza `ValueError`. La mutación pasó a fallar (6 failed).
- Control: la variante *"copiar la matriz y luego normalizar la copia"* (que es **válida**) sigue pasando los 18 tests. Es decir: el test no es demasiado estricto, solo prohíbe tocar el original.

**Las tres que sobreviven por ser "mutantes equivalentes"** (no cambian el comportamiento observable, así que ningún test puede matarlas; no es un hueco):

- *Normalizar dtypes:* pandas ya convierte a `float64` las columnas con `None`/`NaN`; tu versión no lleva esa línea y pasa los 9 tests.
- *Guarda de DataFrame vacío:* agrupar un DataFrame vacío ya da un resultado vacío → `[]`; tu versión no tiene guarda y pasa `test_empty_frame_returns_empty_list`.
- *`merge` inner:* `playlists` sale de las mismas filas y contiene **todos** los `genre_id`, así que inner y left dan lo mismo aquí. `how="left"` sigue siendo mejor porque expresa la intención.

**Un falso fallo del propio tutor (útil como lección).** Tras las 20 mutaciones, la "referencia intacta" mostró 2 tests fallando (`test_top_genres_limit` y `test_limit_applies_after_sorting`). No era un bug: el script restauraba cada archivo con `mv` conservando su fecha antigua, y Python reutilizó **bytecode `.pyc` obsoleto** de la mutación anterior. Se comprobó borrando `__pycache__` y ejecutando 3 veces (153 passed, 1 skipped las tres). La solución en el arnés: `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider` y `touch` al restaurar. Moraleja: un resultado raro en una prueba automatizada puede ser **caché obsoleta**, no el código.

---

## 3. Conceptos enseñados

### 3.1 pandas

#### `DataFrame`, dtypes y `NaN`

Un `DataFrame` es una tabla en memoria con columnas tipadas. Las celdas vacías (de `NULL` en SQL o `None` en Python) se representan como `NaN`. Consecuencia importante: **una columna de enteros con algún `NaN` pasa a `float64`** (por eso `song_id` aparece como `1.0`). Si todos los valores de una columna son `None`, pandas la crea como `object` (el test `test_only_genres_without_songs` cubre ese caso).

#### Un LEFT JOIN multiplica filas ("row multiplication")

Cuando unes género → canciones → playlists, cada canción aparece **una vez por cada playlist** en la que está. Si agregas sin pensar, cuentas y promedias filas repetidas. La pregunta clave antes de agregar es: **¿cuál es el grano de la tabla?** (qué representa cada fila). Aquí el grano es (género, canción, playlist), pero la estadística "duración media" es por **canción**, así que hay que bajar el grano antes de promediar.

Ejemplo del test: Rock tiene canciones de 100 s (en 2 playlists) y 200 s. Promediando filas: `(100+100+200)/3 = 133.3`. Correcto, por canción: `(100+200)/2 = 150.0`.

#### `drop_duplicates(subset=[...])` y por qué la pareja `(genre_id, song_id)`

`drop_duplicates` elimina filas repetidas mirando solo las columnas de `subset`. La pista decía: *un género sin canciones tiene `song_id` vacío*. Y pandas considera que **todos los `NaN` son iguales entre sí**. Si deduplicas solo por `song_id`, Jazz y Blues (ambos `NaN`) se "fusionan" y uno **desaparece** (en el ejemplo, Blues). Con la pareja `(song_id, genre_id)` las filas vacías son distintas porque su `genre_id` lo es. El orden de las columnas en `subset` da igual.

#### `groupby(...).agg(nombre=(columna, función))` — agregación con nombre

```python
per_song.groupby(["genre_id", "name"], as_index=False).agg(
    song_count=("song_id", "count"),
    avg_duration_s=("duration_s", "mean"),
)
```

- Agrupa por género y calcula varias estadísticas a la vez.
- La sintaxis `nombre_salida=(columna_entrada, función)` pone nombre a cada resultado.
- `as_index=False` deja `genre_id` y `name` como **columnas normales** (no como índice), lo que facilita el `merge` posterior.
- Se agrupa por `["genre_id", "name"]` (no solo por `genre_id`) para conservar el nombre en el resultado.

#### `count` vs `size` vs `nunique` (pregunta lateral: *"¿qué es nunique?"*)

`nunique` = *number of unique*: cuenta cuántos valores **distintos** hay, sin repetir y sin contar vacíos. Con la columna `playlist_id` de Rock:

| fila | playlist_id |
|---|---|
| canción 1 | 1 |
| canción 1 | 2 |
| canción 2 | 1 |
| canción 3 | NaN |

| Función | Qué cuenta | Resultado |
|---|---|---|
| `size` | todas las filas | 4 |
| `count` | filas con valor (ignora NaN) | 3 |
| `nunique` | valores distintos (ignora NaN) | 2 (las playlists 1 y 2) |

📝 Comprobado al redactar con una `Series([1, 2, 1, NaN])`: `size 4 | count 3 | nunique 2`.

Por eso:

- `song_count` usa **`count`** sobre `song_id`: Jazz tiene `song_id` vacío → `count = 0` (con `size` saldría 1, un error).
- `playlist_count` usa **`nunique`**: queremos "en cuántas playlists **distintas** aparece el género"; la playlist 1 sale dos veces (porque tiene dos canciones de Rock) y debe contar **una**. El test `test_playlist_counted_once_per_genre` comprueba justo eso.

En SQL equivale a `COUNT(DISTINCT playlist_id)`; de hecho el `get_stats` de artistas ya hacía lo mismo con `func.count(distinct(...))` (ver [[lesson-5]]). Regla: "cuántos X **diferentes**" (usuarios únicos, clientes distintos, playlists distintas) → `nunique`; "cuántas filas / cuántas canciones" → `count` o `size`.

Nota importante: `playlist_count` se calcula sobre `rows` (el original **sin deduplicar**), porque necesita ver las playlists de todas las canciones; `song_count` y `avg_duration_s` se calculan sobre `per_song` (deduplicado).

#### `mean` ignora los vacíos

El promedio de una columna con `NaN` los salta. Para un género sin canciones la media es `NaN` (no hay datos), y luego se convierte a `0.0` con `fillna`.

#### `merge(..., on="genre_id", how="left")`

Une las dos tablas de resultados (estadísticas por canción y recuento de playlists) por la clave `genre_id`. `how="left"` conserva todas las filas de la izquierda aunque no haya pareja. Ver más arriba el comentario sobre que aquí inner y left coinciden.

#### `fillna(0).round(1)`

`fillna(0)` sustituye los vacíos por 0 (géneros sin canciones: duración media 0.0), y `round(1)` deja un decimal (`100.666…` → `100.7`).

#### `sort_values` con varias claves y `ascending` como lista

```python
stats.sort_values(["playlist_count", "song_count", "name"], ascending=[False, False, True])
```

- Ordena por la **primera** columna y solo mira la siguiente cuando hay **empate**.
- `ascending` lleva **un valor por columna**, en la misma posición: `False` = de mayor a menor; `True` = de menor a mayor (A→Z).
- El nombre como último criterio hace el orden **determinista** (sin él, dos géneros empatados saldrían en cualquier orden).

#### `.head(limit)` después de ordenar

`head(n)` toma las primeras n filas **tal como están**. Si lo pones antes de ordenar, recortas un conjunto arbitrario y después ordenas lo que quedó (Rock y Pop en vez de Rock y Folk: error real que detectó el test).

#### `astype` y `to_dict("records")` → tipos de Python

`stats.astype({...}).to_dict(orient="records")` devuelve una **lista de diccionarios** (uno por fila) con `int`/`float`/`str` de Python, justo lo que FastAPI y Pydantic serializan sin problemas. El test `test_returns_plain_python_types` lo vigila.

#### Función pura probada con un `DataFrame` hecho a mano

Como `top_genres` no toca la base, los tests le pasan un DataFrame construido a mano. Ventajas: tests rápidos, sin fixtures, y se puede probar cada caso de borde (vacío, solo géneros vacíos, empates) con 3 líneas.

#### `pd.read_sql(stmt, db.connection())`

Ejecuta una consulta de SQLAlchemy y devuelve un `DataFrame`. Ver el detalle en la sección 2.2.

#### `outerjoin`, `select_from` y `.label`

`outerjoin` = LEFT JOIN (ver la pregunta lateral en 2.2); `select_from` fija la tabla de partida; `.label("genre_id")` renombra la columna de salida para que el DataFrame tenga los nombres esperados y sin choques entre `Genre.id` y `Song.id`.

#### Cuándo pandas y cuándo SQL (pregunta típica de entrevista)

Esta agregación se puede hacer en SQL con `GROUP BY` (ver el equivalente en 2.2) y en producción **sería lo habitual**: la base de datos agrega cerca de los datos y no hay que traer el JOIN completo a memoria. pandas se justifica cuando los datos ya están en memoria, cuando se combinan fuentes distintas o cuando la transformación es incómoda en SQL. En este proyecto pandas sirve para **aprender el patrón** y para tener una función pura fácil de probar.

### 3.2 NumPy

#### Vectores y matrices; `float64`

Una matriz es una tabla numérica de un solo tipo (`dtype`). `np.zeros((filas, columnas))` crea una de ceros en `float64`. Cada fila va a ser una canción y cada columna un "rasgo".

#### One-hot y multi-hot

- **One-hot:** exactamente un `1` por grupo. Una canción tiene **un** género → en las columnas de géneros hay un solo `1`.
- **Multi-hot:** puede haber varios `1`. Una canción puede tener **varios** artistas → en las columnas de artistas hay tantos `1` como artistas.

Con esto "parecerse" se vuelve geometría: dos canciones con los mismos rasgos tienen vectores iguales; sin rasgos en común, vectores "perpendiculares".

#### Similitud coseno

`coseno(a, b) = (a·b) / (|a|·|b|)`. Mide el **ángulo** entre dos vectores, no su tamaño. Con vectores de ceros y unos: `compartidos / √(rasgos_a · rasgos_b)`. Rango `0` a `1` (no hay valores negativos porque no hay componentes negativas). Una canción con muchos rasgos no "gana" solo por tener más, porque se divide por las normas.

#### Orden de las columnas: géneros primero, luego artistas, ambos ordenados

La matriz tiene una columna por cada género distinto y después una por cada artista distinto, **ordenados por id**. El orden es un contrato (el test `test_feature_matrix_layout` lo fija) y hace que `a_col` empiece en `len(g_col)`.

#### Fancy indexing: índices emparejados

```python
m[np.arange(len(songs)), [g_col[g] for _, g in songs]] = 1.0
```

Cuando indexas una matriz con **dos listas**, NumPy las empareja posición a posición y trabaja con las **coordenadas** `(fila_k, columna_k)`; no forma todas las combinaciones. Así una sola línea rellena todos los unos, sin bucle.

#### `np.arange`, `matrix[target]`

`np.arange(n)` = `[0, 1, …, n-1]` (todas las filas). `matrix[target]` es la **fila** `target` (el vector de la canción objetivo).

#### Producto matriz-vector: `matrix @ vector`

`matrix @ matrix[target]` calcula, **de una vez**, el producto punto de cada fila con la objetivo: un vector con un valor por canción (cuántos rasgos comparte cada una con la objetivo). Es la gracia de NumPy: **sin bucles de Python**.

#### Normas: `np.linalg.norm(matrix, axis=1)`

`axis=1` calcula la norma (tamaño del vector) **de cada fila**. `denom = norms * norms[target]` es el denominador de la fórmula del coseno para todas las filas a la vez.

#### Evitar `0/0`: `np.divide(dots, denom, out=np.zeros_like(dots), where=denom!=0)`

Una canción sin rasgos (vector cero) tiene norma 0 y la división daría `NaN` y un `RuntimeWarning`. `np.divide` con:

- `where=cond` → solo divide donde la condición es verdadera;
- `out=np.zeros_like(dots)` → donde no divide, deja el valor de `out`: `0.0`.

📝 Comparación real con un vector cero entre los candidatos:

```
dots / denom           → [1.  1.  0.7071  0.  nan]   + RuntimeWarning: invalid value encountered in divide
np.divide(..., where)  → [1.  1.  0.7071  0.  0. ]    sin warning
```

El test `test_zero_vectors_do_not_warn_or_produce_nan` usa `warnings.simplefilter("error")` para que cualquier warning rompa el test.

#### `np.argsort(-scores, kind="stable")`

- `argsort` devuelve los **índices** que ordenarían el array, de menor a mayor. Para ordenar de mayor a menor se le pasa `-scores` (signo cambiado).
- **`kind="stable"`**: en un empate, mantiene el **orden original** (por fila, que es por id). Sin él, el orden de los empates no está garantizado.
- 📝 Medición al redactar: con `np.ones(n)` el orden por defecto conservó el orden en mi entorno, pero con una mezcla de empates (60 valores aleatorios entre 3 posibles) el `argsort` por defecto **sí difirió** del estable. En la máquina de validación del tutor, las 40 filas idénticas ya bastaban para delatar la mutación. Moraleja: el comportamiento de un orden inestable **depende del tamaño, de los datos y de la CPU**; no te apoyes en él, usa `kind="stable"`.

#### La lista final: `int(i)`, `float(...)` y el filtro

```python
ranked = [(int(i), float(scores[i])) for i in order if i != target and scores[i] > 0]
return ranked[:limit]
```

- `i != target` → fuera la propia canción (siempre sale con score 1.0).
- `scores[i] > 0` → fuera las que no comparten nada.
- `int(i)` / `float(...)` → convierten `np.int64`/`np.float64` a tipos de Python. 📝 `isinstance(np.int64(1), int)` es `False`; si no se convierten, la serialización a JSON de FastAPI/Pydantic puede fallar o comportarse distinto.
- `[:limit]` → recorte **después** de filtrar y ordenar.

#### No mutar la entrada (`setflags(write=False)`)

Una función pura no modifica sus argumentos. Si `top_similar` hiciera `matrix /= ...` (normalizar en el sitio), **dañaría la matriz del llamador**. El test usa una matriz de solo lectura (`M.setflags(write=False)`): cualquier escritura in-situ lanza `ValueError: output array is read-only`. (Copiar y modificar la copia sí es válido.)

#### El índice de fila NO es el id de la canción (`row_of`)

La fila 0 de la matriz es "la primera canción de la lista", no "la canción 0". Para pasar de **id de canción** a **fila** se usa un diccionario `row_of = {sid: i for i, (sid, _, _) in enumerate(rows)}`. Confundirlos es un error **silencioso** cuando los ids son `1..n` (solo se desplaza una posición y el resultado es de otra canción). Es el mismo patrón que `feature_matrix` usa por dentro (`row_of`, `g_col`, `a_col`: diccionarios "valor del mundo real → posición en la matriz").

#### Dónde se redondea (`round(score, 4)` en el servicio)

`top_similar` devuelve los números sin tocar (útil para tests con `pytest.approx`); el formato de la respuesta (4 decimales, como dice el README) se decide **una capa más arriba**, en `similar_songs`.

#### Coste y qué haría una versión de producción

Cada petición hace `list_song_rows` + `list_song_artist_links` y **reconstruye la matriz entera**. Para un ejercicio está bien. En producción: precalcular y **cachear** la matriz (o los vectores), o usar una base de vectores como **pgvector** (extensión de PostgreSQL) o **FAISS** (librería de búsqueda de vecinos cercanos). Eso es lo que hay que decir en la entrevista.

#### Sintaxis de Python que aparecieron por el camino

- **Comprensión de conjunto** `{g for _, g in songs}` → valores **únicos** (sin `{ }` aparece un generador y el artista se repite).
- **Comprensión de diccionario** `{g: j for j, g in enumerate(genre_ids)}`.
- **`enumerate`** devuelve `(posición, valor)`, en ese orden.
- **Desempaquetado con `_`**: `for _, g in songs` ignora el primer elemento de cada tupla.
- **`sorted(...)`** de un conjunto devuelve una lista ordenada.
- **Argumentos por nombre**: `top_similar(matrix=matrix, target=target, limit=limit)` exige que los nombres coincidan con los de la definición.

### 3.3 Arquitectura y herramientas

- **Capas:** `routers/` (HTTP: códigos de estado, validación de `Query`, 404), `services/` (reglas y cálculo, funciones puras), `repositories/` (SQL). Por eso se pudo probar `top_genres`, `feature_matrix` y `top_similar` **sin base de datos**.
- **El 404 vive en el router:** el servicio `similar_songs` asume que la canción existe (hace `row_of[song_id]`, que daría `KeyError` si no); el router comprueba antes con `get_song`.
- **Lista vacía ≠ error:** una canción aislada devuelve `200 []` (como en [[lesson-5]]); solo un id inexistente da 404.
- **`response_model=list[GenreStats]` / `list[SimilarSong]`:** FastAPI valida y filtra la salida con el schema.
- **`Query(5, ge=1, le=50)`:** valida el parámetro; fuera de rango → **422** con el sobre de error del proyecto.
- **`uv add`:** instala y deja registrado en `pyproject.toml` + `uv.lock`.
- **Errores de colección de pytest:** si un módulo falla al importarse, pytest se interrumpe antes de ejecutar nada ("Interrupted: N errors during collection"); `--ignore=archivo` o ejecutar un archivo concreto permite avanzar.
- **`uv run python -c "import app.main"`:** atajo para detectar errores de importación sin levantar el servidor.
- **`uvx ruff check --select F,E9 app tests`:** red de seguridad rápida (nombres sin definir, imports sin usar, sintaxis) con sus límites (ver 2.0).

---

## 4. Errores cometidos y diagnóstico

| # | Síntoma / traza | Causa | Arreglo | Lección |
|---|---|---|---|---|
| 1 | `ERROR tests/test_similarity.py … ModuleNotFoundError: No module named 'numpy'` y lo mismo con `pandas`; `Interrupted: 2 errors during collection` | Librerías sin instalar; los tests las importan en la primera línea | `uv add pandas numpy` y commitear `pyproject.toml` + `uv.lock` | Un error de colección no es un fallo de tu código: pytest ni llega a ejecutar tests |
| 2 | Línea 17 `sort_values([...], ascending=[...])` sin completar | No traducir "playlists ↓, canciones ↓, nombre ↑" a columnas + `ascending` | `["playlist_count","song_count","name"]` con `[False, False, True]` | La lista `ascending` lleva un valor por columna, en el mismo orden |
| 3 | 9 tests fallan con `AttributeError: 'DataFrame' object has no attribute 'groupvy'. Did you mean: 'groupby'?` | Typo en el método | `groupby` | Lee el final del mensaje: Python ya sugiere la corrección. Ruff no detecta typos de atributos |
| 4 | `import numpy as numpy` | Alias equivocado; el código usa `np` | `import numpy as np` | Ruff lo marca como `F821` (nombre no definido); sin él, `NameError` |
| 5 | `artist_ids = sorted(a for _, a in links)` | Faltan las llaves del conjunto: el artista 7 sale duplicado | `sorted({a for _, a in links})` | Un conjunto elimina duplicados; `sorted` sobre un generador no |
| 6 | `a_col = {a: len(g_col) + j for a, j in enumerate(artist_ids)}` | `enumerate` devuelve `(posición, valor)`, y estaba al revés | `for j, a in enumerate(artist_ids)` | Si lo dejas, `a_col[a]` da `KeyError`. Fíjate en cómo lo hiciste bien en `g_col` |
| 7 | `np.argsort(scores, kind="stable")` | `argsort` ordena de menor a mayor | `np.argsort(-scores, kind="stable")` | Para orden descendente, cambia el signo |
| 8 | `target = song_id` | Se confunde el **id** de la canción con la **fila** de la matriz | `row_of = {sid: i …}` y `target = row_of[song_id]` | Error silencioso mientras los ids sean `1..n`; con huecos daría `IndexError` |
| 9 | `top_similar(matrix=matrix, song_id=target, …)` → `TypeError: unexpected keyword argument 'song_id'` | El parámetro se llama `target` | `target=target` | Ruff no valida los nombres de argumentos |
| 10 | Respuesta con `0.816496580927726` en vez de `0.8165` | Falta `round(score, 4)` en el servicio | `"score": round(score, 4)` | El formato de la respuesta se decide en la capa del servicio |
| 11 | *(Tutor)* Tras las mutaciones, la referencia "intacta" falló 2 tests | Bytecode `.pyc` obsoleto del arnés de mutaciones | Borrar `__pycache__`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider` | Un resultado raro en pruebas automatizadas puede ser caché |
| 12 | *(Tutor)* Dos mutaciones sobrevivieron (orden estable y mutar la matriz) | Tests demasiado débiles | 40 filas idénticas, normas ≠ 1 y matriz de solo lectura | Un test que no puede fallar no protege nada |

---

## 5. Cómo se relaciona con el ritme (README, proyecto y entrevista)

**Con el README (el "ritme" del proyecto)**

- Cubre la **Fase 2** del contrato: las dos filas `GET /stats/top-genres` (200 `list[GenreStats]`, 422) y `GET /songs/{song_id}/similar` (200 `list[SimilarSong]`, 404, 422), y las dos filas de la tabla de schemas (`GenreStats`, `SimilarSong`).
- Marca la casilla *"pandas: `/stats/top-genres` · NumPy: `/songs/{id}/similar`"* del checklist "Orden de construcción".
- Respeta las reglas transversales: paginación `limit` (aquí 1–50, por defecto 5), errores con el sobre `{"error": {...}}` y rutas públicas (sin autenticación).
- Alcance del README: *"canciones en las que participa un artista y en cuántas playlists aparece"* ya estaba en `ArtistStats`; `top-genres` es la versión por género de esa misma idea (`COUNT(DISTINCT …)` → `nunique`).

**Con el resto del proyecto**

- Reutiliza los modelos de [[lesson-3]] (`Genre`, `Song`, `SongArtist`, `PlaylistSong`) y la semilla.
- Reutiliza el patrón de capas de [[lesson-5]] y [[lesson-6]] y el sobre de errores (422 de `Query`, 404).
- Los tests reutilizan `db_factory` y `client` de `conftest.py` ([[lesson-1]]/[[lesson-3]]): base SQLite en archivo temporal (porque `TestClient` ejecuta los endpoints en otro hilo y `:memory:` serían bases distintas) y `dependency_overrides` para inyectarla.
- `GET /songs/{song_id}/similar` es lo que React podría consumir más adelante ([[lesson-9]]); CORS ya permite el origen `http://localhost:5173`.

**Con la entrevista (lo que ya puedes explicar)**

- **pandas:** por qué un LEFT JOIN multiplica filas y cómo deduplicar antes de promediar; diferencia entre `count`, `size` y `nunique`; cuándo conviene hacerlo en SQL con `GROUP BY`.
- **NumPy:** representar canciones como vectores (one-hot + multi-hot), calcular la similitud coseno sin bucles, y las trampas: división por cero, orden estable, tipos de NumPy frente a los de Python, no mutar la entrada.
- **Arquitectura:** funciones puras en `services/`, consultas en `repositories/` y HTTP solo en los routers. Por eso pudiste probar todo sin base de datos.
- **Producción:** matriz recalculada en cada petición → cachear/precalcular o usar pgvector/FAISS.

---

## 6. Preguntas de entrevista

1. **¿Por qué un LEFT JOIN "multiplica" filas y qué consecuencia tiene al agregar?**
   Porque cada fila del lado "uno" se repite por cada pareja del lado "muchos". Si promedias o cuentas sin deduplicar, cuentas la misma entidad varias veces (Rock daría 133.3 s en vez de 150.0 s). Hay que bajar al grano correcto antes de agregar (`drop_duplicates` en pandas, subconsulta o CTE en SQL).

2. **¿Diferencia entre `count`, `size` y `nunique` en pandas?**
   `size` cuenta todas las filas; `count` cuenta las no nulas; `nunique` cuenta los valores distintos no nulos. Con `[1, 2, 1, NaN]`: 4, 3 y 2. Para "playlists distintas" se usa `nunique` (= `COUNT(DISTINCT …)` en SQL).

3. **¿Por qué `outerjoin` y no `join` para el ranking de géneros?**
   Porque el contrato exige incluir géneros sin canciones (con ceros). Un INNER JOIN los descarta sin avisar. Regla: "todos los X, tengan o no Y" → LEFT JOIN desde X.

4. **¿Por qué `drop_duplicates` debe usar `(genre_id, song_id)` y no solo `song_id`?**
   Porque pandas trata todos los `NaN` como iguales: los géneros sin canciones (todos con `song_id` vacío) se fusionarían y desaparecerían.

5. **¿Harías esta agregación en pandas o en SQL en producción?**
   En SQL (`GROUP BY` con dos agregaciones y LEFT JOIN): agrega cerca de los datos y no trae el JOIN completo a memoria. pandas se justifica con datos ya en memoria, fuentes mezcladas o transformaciones incómodas en SQL.

6. **Explica la similitud coseno y por qué sirve aquí.**
   Mide el ángulo entre dos vectores: `(a·b)/(|a||b|)`. Con vectores de ceros y unos es `compartidos/√(rasgos_a·rasgos_b)`. No premia a las canciones con más rasgos porque normaliza por el tamaño.

7. **¿Cómo evitas la división por cero cuando hay vectores nulos?**
   `np.divide(a, b, out=np.zeros_like(a), where=b > 0)`: divide solo donde el denominador es positivo y deja 0 en el resto; sin `NaN` ni `RuntimeWarning`.

8. **¿Por qué `argsort(-scores, kind="stable")`?**
   El signo menos da el orden descendente; `stable` garantiza que los empates conservan el orden original (por id), de modo que la respuesta es determinista.

9. **¿Por qué convertir con `int()` y `float()` los resultados de NumPy?**
   `np.int64` y `np.float64` no son los tipos nativos de Python (`isinstance(np.int64(1), int)` es `False`); conviene devolver tipos nativos para serializar a JSON y para que los tests/Pydantic se comporten de forma predecible.

10. **¿Qué diferencia hay entre el índice de fila y el id de una canción?**
    El id es la identidad en la base; la fila es la posición en la matriz. Se traducen con un diccionario `row_of`. Confundirlos da resultados de otra canción sin ningún error.

11. **¿Qué problema tiene reconstruir la matriz en cada petición y cómo lo resolverías?**
    Coste O(canciones × rasgos) por petición. Solución: precalcular y cachear los vectores, o usar una base vectorial (pgvector, FAISS).

12. **¿Qué es un "mutante superviviente" en un test de mutaciones?**
    Una versión rota a propósito del código que sigue pasando los tests. O indica un test débil (hay que endurecerlo) o un *mutante equivalente* (el cambio no altera el comportamiento observable).

---

## 7. Checklist / estado

**Hecho**

- [x] `uv add pandas numpy` (con `pyproject.toml` y `uv.lock` actualizados)
- [x] Paso 1: `app/services/stats.py` → `top_genres` (9 passed)
- [x] Paso 2: `repositories/stats.py`, `routers/stats.py`, `GenreStats`, `main.py` (7 passed; 16 con el Paso 1)
- [x] Paso 3: `app/services/similarity.py` → `feature_matrix` y `top_similar` (10 passed)
- [x] Paso 4: `list_song_rows`, `list_song_artist_links`, `similar_songs`, `SimilarSong` y `GET /songs/{song_id}/similar` (8 passed)
- [x] Suite completa: **153 passed, 1 skipped**; ruff limpio; `import app.main` correcto
- [x] README: filas de contrato para `/stats/top-genres` y `/songs/{id}/similar`, filas de schemas y casilla marcada
- [x] Commit con `pyproject.toml` y `uv.lock`

**Observaciones sobre el código actual del repo 📝** (comprobadas al redactar; no son fallos de los tests, son pulido pendiente)

- [ ] **`list_song_rows` no lleva `.order_by(models.Song.id)`**, y el enunciado decía que las canciones debían salir ordenadas por id porque "el orden de las filas decide el desempate". Los tests pasan porque SQLite suele devolver las filas por `rowid`, pero **sin `ORDER BY` el orden no está garantizado** (en PostgreSQL, por ejemplo, el desempate podría variar). Añadir: `select(...).order_by(models.Song.id)`.
- [ ] **Mensaje del 404 con typo:** `f"Song {song_id} not fount"` → `not found` (el test solo comprueba que contenga `"99"`, por eso pasa).
- [ ] **README: filas de schemas duplicadas.** `GenreStats` y `SimilarSong` aparecen dos veces (líneas 94–97). Borrar las dos repetidas.
- [ ] (Opcional) `top_genres`: el `astype` con `"avg_duration_s": float` es redundante, y los dos `rows`/`stats` se podrían nombrar más claro. Funciona igual.

**Pendiente a futuro**

- [ ] Profundizar en middlewares (el usuario pidió dejarlo "para más adelante"; ver [[lesson-9]]).
- [ ] Dockerfile ([[lesson-7]]).

---

## Apéndice · Comandos de la lección (chuleta)

```bash
cd backend
uv add pandas numpy                                   # instala y registra en pyproject.toml + uv.lock
uvx ruff check --select F,E9 app tests                # nombres sin definir / sintaxis (no ve typos de atributos)
uv run python -c "import app.main"                    # detecta errores de import sin levantar el servidor

uv run pytest tests/test_stats_service.py -q          # Paso 1 → 9 passed
uv run pytest tests/test_stats_api.py -q              # Paso 2 → 7 passed
uv run pytest tests/test_similarity.py -q             # Paso 3 → 10 passed
uv run pytest tests/test_similar_api.py -q            # Paso 4 → 8 passed
uv run pytest -q                                      # suite completa → 153 passed, 1 skipped

# mientras faltan pasos, para comprobar que el resto no se rompió:
uv run pytest -q --ignore=tests/test_stats_service.py --ignore=tests/test_stats_api.py \
  --ignore=tests/test_similarity.py --ignore=tests/test_similar_api.py      # 119 passed, 1 skipped
```

📝 Prueba manual con la API levantada (`uv run uvicorn app.main:app --reload`); estas llamadas no se ejecutaron en clase:

```bash
curl "localhost:8000/stats/top-genres?limit=3"
curl "localhost:8000/songs/2/similar?limit=3"
curl "localhost:8000/songs/9999/similar"      # 404 con el sobre de error
curl "localhost:8000/stats/top-genres?limit=0" # 422
```

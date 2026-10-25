---
tags: [fullstack-project-music, leccion, en-curso]
leccion: 9
estado: en-curso
---

# Lección 9 · CORS y arranque de React

> **Objetivo:** que el navegador (React en `:5173`) pueda hablar con la API (FastAPI en `:8000`), y arrancar el frontend con Vite hasta tener el primer componente (`SongList`) que pide `GET /songs`.
> **Estado al escribir esto:** CORS terminado y con tests (4 en verde); proyecto Vite creado y verificado; `SongList` **dado pero todavía sin escribir** (el archivo `src/SongList.jsx` existe y está vacío). Los pasos 3–5 de React siguen pendientes (ver sección 7).

## 0. Dónde encaja

- Es el **octavo bloque** del plan, justo después de [[lesson-8]] (pandas + NumPy) y con el backend ya cerrado: **153 passed, 1 skipped**, ruff limpio y `import app.main` correcto.
- El tutor la llamó **"Lección 9"** (el docstring de `tests/test_cors.py` dice literalmente `"""Lección 9: CORS …"""`). En el diálogo la numeración no coincide con los nombres de archivo de estas notas, por eso aquí es `lesson-9`.
- Cubre dos líneas del README:
  - la del stack: "…**React (Vite)** · un solo Dockerfile al final";
  - la del checklist: `- [ ] React: SongList, LoginForm` (todavía **sin marcar**: solo hay medio `SongList`).
- Dependencias con otras lecciones:
  - [[lesson-4]] (auth): el `Bearer` y el `POST /auth/login` que React llamará en el Paso 4 son los de esa lección.
  - [[lesson-5]] (canciones y sobre de errores): la forma de `GET /songs` y la regla "lista vacía = `200 []`" que React usa para el estado "vacío".
  - [[lesson-6]] (playlists): las rutas autenticadas que React llamará en el Paso 5.
  - [[lesson-7]] (Dockerfile, pendiente): el origen permitido de CORS debería salir de una variable de entorno en el contenedor.
- **"El ritme"** = el README del proyecto, el plan de entrenamiento y la entrevista. El tutor lo remarcó: React "es la parte que más pesa en la entrevista en vivo".

### Plan de la lección (tabla del tutor)

| Paso | Qué | Tiempo | Estado |
|---|---|---|---|
| 0 | CORS en el backend | 10 min | **hecho** (4 tests en verde) |
| 1 | Crear el proyecto Vite y verlo corriendo | 10 min | **hecho** (ambos servidores verificados) |
| 2 | `SongList`: fetch, cargando/error/vacío | 40 min | **en curso** (enunciado dado, archivo vacío) |
| 3 | Búsqueda con `q` (input controlado) | 20 min | pendiente |
| 4 | `LoginForm` y guardar el token | 40 min | pendiente |
| 5 | Llamada autenticada con `Bearer` | 20 min | pendiente |

Total estimado por el tutor para React: **~2,5 h**.

## 1. Qué se hizo (resumen)

1. El tutor escribió **antes que el código** `tests/test_cors.py` (4 tests) y lo validó en una copia temporal con una implementación de referencia y dos mutaciones. Sin middleware fallaban 3 de 4.
2. Tú corriste la suite: **3 fallos** (los tres de CORS). Añadiste `CORSMiddleware` en `app/main.py`: `test_cors.py` pasó a **4 passed**.
3. Quedaron "dos errores" más: no eran de CORS, sino **errores de colección** porque los tests de pandas/NumPy ([[lesson-8]]) importan librerías aún no instaladas. Se resolvió con `uv add pandas numpy`.
4. Preguntaste qué hace exactamente el bloque `add_middleware(...)` y si el `"*"` de `allow_methods`/`allow_headers` significa "todo". Decidimos **dejarlo así por ahora** y volver a los middlewares más adelante.
5. Cerrado el backend, se creó el frontend: `npm create vite@latest . -- --template react` (carpeta no vacía → "Ignore files and continue"; linter → **ESLint**), `npm install`, `npm run dev`. Verificaste los dos servidores a la vez.
6. Preguntaste cómo se relacionan **JavaScript, Node.js y React**; después describiste lo que habías visto en la carpeta y el tutor lo corrigió (qué comando crea qué).
7. El tutor dio el **Paso 2**: `SongList.jsx` con huecos (`res.status`, `[]`, `key=`) y los cuatro estados de UI.

## 2. Paso a paso

### 2.0 Prerrequisito: una lista vacía es `200 []`

Antes de empezar React el tutor te pidió limpiar `routers/songs.py`. Había quedado esto (ver [[lesson-5]]):

```python
songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
if songs is None or []:
    raise HTTPException(status_code=404, detail="No songs found")   # luego lo cambiaste a 200
return songs
```

Tu pregunta fue si la corrección era cambiar el `404` por `200`. Respuesta del tutor: **no, hay que borrar las dos líneas** (el `if` y el `raise`):

```python
songs = songs_repo.list_songs(db, genre_id, artist_id, q, limit, offset)
return songs
```

Por qué:

- **`raise HTTPException` no es para respuestas buenas.** Con `raise`, FastAPI pasa por el manejador de errores y devolvería el sobre `{"error": {...}}` con código 200: un error mezclado con un éxito.
- **Una lista vacía ya es una respuesta válida.** `return songs` con `[]` da `200 []`, que es lo que dice el contrato y lo que **React espera para pintar "No hay canciones"**.
- **La condición nunca fue "lista vacía".** `songs is None or []` se lee `(songs is None) or []`; el `[]` final siempre es falso, así que equivale a `songs is None`. Como el repositorio siempre devuelve una lista, no se cumplía nunca: código muerto.
- `HTTPException` se sigue importando porque `create_song` la usa.

Estado actual del repo: las dos líneas están **comentadas** (`#if songs is None or []:` / `#    raise HTTPException(status_code=200, …)`). Funciona igual; el tutor recomendó borrarlas del todo.

### 2.1 Paso 0 — CORS en el backend

#### 2.1.1 Primero los tests (los escribió el tutor)

El tutor dejó escrito y validado `backend/tests/test_cors.py` **antes** de explicarte nada, para que tú solo tuvieras que hacer que pasaran:

```python
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
```

Qué protege cada test:

| Test | Qué simula | Qué falla si el middleware está mal |
|---|---|---|
| `test_preflight_allows_frontend_origin_and_headers` | El `OPTIONS` previo que manda el navegador antes de un `POST /auth/login` con JSON y `Authorization`. | Sin middleware responde **405** (la ruta solo admite `POST`). Con `allow_headers` mal, la respuesta no lista `authorization`. |
| `test_normal_request_carries_cors_header` | La petición real (`GET /songs`) desde React. | No hay cabecera `Access-Control-Allow-Origin` → el navegador no deja a React **leer** la respuesta. |
| `test_error_responses_also_carry_cors_header` | Un `401` (`GET /me` sin token). | Si el error no lleva la cabecera, el navegador lo oculta y React solo ve "Network Error", sin saber que era un 401. |
| `test_unknown_origin_gets_no_cors_header` | Una web que no es la nuestra (`evil.example`). | Con `allow_origins=["*"]` este test falla: se estaría autorizando a cualquiera. |

Detalle importante: **`TestClient` no es un navegador**. No aplica ninguna regla CORS, pero sí deja enviar la cabecera `Origin` a mano. Por eso los tests comprueban lo único que la API controla: **qué cabeceras `Access-Control-*` devuelve**.

#### 2.1.2 Cómo se validaron los tests (sin tocar tu código)

El tutor trabajó en una copia temporal (`rsync` sin `.venv`, caches ni `*.db`), puso la implementación de referencia y probó mutaciones:

| Situación | Resultado real |
|---|---|
| Sin middleware | `3 failed, 1 passed` (`KeyError: 'access-control-allow-origin'` en dos; el preflight falla; pasa solo el de "origen desconocido", porque sin middleware tampoco hay cabecera) |
| Con el middleware de referencia | `4 passed` |
| Mutación: `allow_origins=["*"]` | `4 failed` (la cabecera pasa a ser `*` en vez del origen, y el origen desconocido también la recibe) |
| Mutación: quitar `allow_headers` | `1 failed, 3 passed` (el preflight falla en `assert "authorization" in allowed`: `Authorization` no es una cabecera "simple" y hay que autorizarla) |
| Suite completa con referencia | `119 passed, 1 skipped`; ruff limpio |

Cuentas de la suite: 115 (backend de playlists cerrado) + 4 (CORS) = **119**; luego +34 de pandas/NumPy ([[lesson-8]]) = **153**.

#### 2.1.3 Tu primer resultado: "3 errores"

Pegaste que tenías 3 fallos. El tutor corrió la suite en una copia y salió:

```
E       assert 405 == 200
E        +  where 405 = <Response [405 Method Not Allowed]>.status_code
E       KeyError: 'access-control-allow-origin'
E       KeyError: 'access-control-allow-origin'
FAILED tests/test_cors.py::test_preflight_allows_frontend_origin_and_headers
FAILED tests/test_cors.py::test_normal_request_carries_cors_header - KeyError...
FAILED tests/test_cors.py::test_error_responses_also_carry_cors_header - KeyE...
3 failed, 116 passed, 1 skipped in 5.90s
```

Lectura de la traza:

- **`405 == 200`**: el preflight es un `OPTIONS /auth/login`. Sin middleware, FastAPI busca esa ruta con método `OPTIONS`, no existe y devuelve *405 Method Not Allowed*.
- **`KeyError: 'access-control-allow-origin'`**: el test pide `r.headers["access-control-allow-origin"]` y esa cabecera no está en la respuesta.
- Ruff estaba limpio (`All checks passed!`) y `list_songs` estaba bien; los 3 fallos eran exactamente los 3 tests de CORS: **solo faltaba el middleware**.

#### 2.1.4 El código que se añade a `app/main.py`

El tutor dio el patrón con huecos (`allow_origins=[...]` etc.) y las pistas: "solo el origen del front, **no** `"*"`" y "para métodos y cabeceras basta `["*"]`". La solución:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Music-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Así quedó tu `main.py` (estado actual del repo, ya con el router de estadísticas):

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import artists, auth, genres, playlists, songs, users, stats

app = FastAPI(title="Music-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


router_list = [artists, auth, genres, playlists, songs, users, stats]
for r in router_list:
    app.include_router(r.router)
```

Comandos de comprobación:

```bash
uv run pytest tests/test_cors.py -q      # 4 passed
uv run pytest -q                          # 119 passed, 1 skipped (antes de la lección de pandas/NumPy)
uvx ruff check --select F,E9 app tests    # All checks passed!
```

#### 2.1.5 Tu segundo resultado: "aún dos errores" (no eran de CORS)

Tras colocar el middleware, `test_cors.py` daba **4 passed** y ruff limpio. Los "dos errores" venían de ejecutar la suite completa:

```
ERROR tests/test_similarity.py     → ModuleNotFoundError: No module named 'numpy'
ERROR tests/test_stats_service.py  → ModuleNotFoundError: No module named 'pandas'
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
```

- Son **errores de colección**: pytest importa cada archivo de tests antes de ejecutarlos; si un `import` falla, aborta (*Interrupted: 2 errors during collection*) y no corre nada.
- Esos dos archivos pertenecen a la lección nueva ([[lesson-8]]) e importan `numpy` y `pandas` en su primera línea; todavía no estaban instalados.
- Arreglo:

```bash
cd backend
uv add pandas numpy        # modifica pyproject.toml y uv.lock → hay que commitearlos
```

- Mientras no existiera el código de la lección, para comprobar que lo demás seguía sano:

```bash
uv run pytest -q --ignore=tests/test_stats_service.py --ignore=tests/test_stats_api.py \
  --ignore=tests/test_similarity.py --ignore=tests/test_similar_api.py
# 119 passed, 1 skipped
```

#### 2.1.6 Qué hace cada línea (tu pregunta: "explícame qué hace este código")

Ver el desarrollo conceptual en la sección 3.1. Resumen de la respuesta: el bloque le dice a la API **qué páginas web tienen permiso para llamarla desde el navegador**; es una regla del navegador y no de la API; el middleware contesta solo el preflight sin llegar a tus rutas.

#### 2.1.7 Tu pregunta del asterisco y la decisión final

Preguntaste: "¿ese asterisco significa que todos los métodos son permitidos?". Respuesta: **sí** (`allow_methods=["*"]` permite GET, POST, PUT, PATCH, DELETE, HEAD y OPTIONS; `allow_headers=["*"]` cualquier cabecera), con tres matices (ver 3.1). Tu decisión: **"por ahora dejemos esta parte así; profundizaremos en los middlewares más adelante"**. El tutor lo anotó como tema pendiente (ver sección 8).

### 2.2 Cierre del backend (antes de React)

Con pandas/NumPy en verde, el tutor verificó el conjunto:

```
153 passed, 1 skipped in 6.74s
All checks passed!
import-ok
```

Y dejó tres tareas de README de 5 minutos (detalle en [[lesson-8]]): añadir a la tabla del contrato `GET /stats/top-genres` y `GET /songs/{song_id}/similar`, añadir `GenreStats` y `SimilarSong` a la tabla de schemas, marcar `pandas/NumPy` (y `Playlists` si faltaba) y **commitear incluyendo `pyproject.toml` y `uv.lock`**.

Resumen que dio de "lo que ya puedes explicar en la entrevista": pandas (join multiplica filas, `count`/`size`/`nunique`, cuándo hacerlo en SQL), NumPy (vectores, coseno sin bucles, división por cero, orden estable, tipos NumPy vs Python) y la arquitectura (funciones puras en `services/`, SQL en `repositories/`, HTTP solo en routers).

### 2.3 Paso 1 — Crear el proyecto con Vite

#### Requisito y comandos

Necesitas **Node 20 o superior** (`node -v`; en tu máquina ahora mismo `v22.23.4`, npm `10.9.9`). Desde la raíz del repo:

```bash
cd frontend
npm create vite@latest . -- --template react    # el "." = en esta carpeta; --template react = plantilla React
npm install                                       # descarga las dependencias a node_modules/
npm run dev                                       # servidor de desarrollo en http://localhost:5173
```

En otra terminal, la API:

```bash
cd backend
uv run uvicorn app.main:app --reload              # http://localhost:8000
```

#### Las preguntas que hizo el asistente de `create vite`

| Pregunta | Qué contestaste / qué dijo el tutor | Por qué |
|---|---|---|
| `Current directory is not empty. Please choose how to proceed:` | **Ignore files and continue** | `frontend/` ya contenía un `.gitkeep` (la carpeta existía para versionarla vacía). Vite avisa de que no está vacía; "ignorar" mantiene tus archivos y escribe la plantilla encima. |
| `Which linter to use?` (Oxlint / ESLint) | **ESLint** | Es el estándar en casi todos los proyectos de React y el que verás en la mayoría de bases de código y entrevistas. Oxlint es más rápido pero más nuevo; para este ejercicio no cambia nada. |
| Opciones "experimentales" (Rolldown, compilador de React) | **No** | Fuera de alcance; no aportan a lo que se evalúa. |
| `Install with npm and start now?` | **Yes** (opcional) | Ahorra los dos comandos siguientes (`npm install` + `npm run dev`). |

Salida esperada del servidor de desarrollo: `Local: http://localhost:5173/`.

#### Comprobación de los dos servidores

1. `http://localhost:8000/songs` devuelve JSON (backend vivo).
2. `http://localhost:5173` muestra la página de plantilla de Vite (frontend vivo).

Tu mensaje: "las comprobaciones de los dos servidores para el frontend y para el backend están adecuadas". Paso 1 terminado.

#### Lo que generó la plantilla (estado real del repo)

```
frontend/
  .gitignore            # node_modules, dist, logs, editores…
  .gitkeep              # el de antes
  README.md             # README de la plantilla de Vite (no el del proyecto)
  index.html            # la única página HTML; carga /src/main.jsx
  package.json          # equivale a pyproject.toml
  package-lock.json     # equivale a uv.lock
  eslint.config.js      # reglas de lint
  vite.config.js        # configuración de Vite (plugin de React)
  public/               # archivos estáticos tal cual (favicon.svg, icons.svg)
  src/
    main.jsx            # punto de entrada (equivale a main.py)
    App.jsx             # componente raíz (aún con la plantilla de Vite)
    SongList.jsx        # creado por ti para el Paso 2 (vacío por ahora)
    App.css, index.css
    assets/             # hero.png, react.svg, vite.svg
  node_modules/         # las librerías descargadas (no se commitea)
```

`package.json`:

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.3.1",
    "react-dom": "^19.3.1"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.1",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.1.2",
    "eslint": "^10.13.0",
    "eslint-plugin-react-hooks": "^7.1.1",
    "eslint-plugin-react-refresh": "^0.5.7",
    "globals": "^17.13.0",
    "vite": "^8.3.4"
  }
}
```

- `"scripts"` son los comandos que lanzas con `npm run <nombre>` (`dev`, `build`, `lint`, `preview`).
- `"dependencies"` es lo que necesita la app en ejecución (`react`, `react-dom`); `"devDependencies"` es solo herramientas de desarrollo (Vite, ESLint…). Es el equivalente a `uv add` frente a `uv add --dev`.
- `"type": "module"` hace que los `.js` usen `import`/`export` (módulos ES), como en el navegador.

`index.html` (fragmento relevante) y `src/main.jsx`:

```html
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
```

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

Flujo: el navegador pide `index.html` → carga `main.jsx` → React monta `<App />` dentro de `<div id="root">`. Fíjate en `<StrictMode>`: es la razón de que en desarrollo veas el `fetch` dos veces (ver 3.4).

`eslint.config.js` activa `js.configs.recommended`, `eslint-plugin-react-hooks` (reglas de hooks, incluida la de dependencias de `useEffect`) y `eslint-plugin-react-refresh`. Se ejecuta con `npm run lint`.

`vite.config.js`: solo registra `@vitejs/plugin-react` (traduce JSX y activa el *hot reload*).

### 2.4 La pregunta: "¿qué diferencia hay entre Node.js y React? ¿qué tienen que ver con JavaScript?"

Ver 3.2 para el desarrollo completo (tabla de equivalencias con Python, diagrama de los dos servidores y puntos de entrevista).

### 2.5 Tu descripción de las carpetas y la corrección

Dijiste, en tus palabras: React "orquesta JavaScript y HTML": el HTML como template/parte visual y JavaScript como lo que mueve las cosas; y que al ejecutar `npm run build` aparecieron `node_modules`, `public`, `src`… "un template general del dev que es estándar en el frontend".

Corrección del tutor ("casi"):

- **Sobre React:** no hay un archivo HTML aparte como plantilla. El "HTML" se escribe **dentro** del JavaScript (JSX) y cada componente es una función que devuelve lo que se ve. La idea central: **la interfaz es una función del estado**.
- **Sobre las carpetas:** salieron de **comandos distintos**, no de `npm run build`:

| Comando | Qué creó | Equivalente en tu backend |
|---|---|---|
| `npm create vite` | la plantilla: `src/`, `public/`, `index.html`, `package.json`, `eslint.config.js` | la estructura inicial de `uv init` |
| `npm install` | `node_modules/` (las librerías descargadas) | `.venv/` (no se commitea) |
| `npm run build` | `dist/`, los archivos finales para producción | no tiene equivalente directo |

- Y sí: es la **plantilla estándar** que da Vite para empezar.
- Otras equivalencias: `package.json` ↔ `pyproject.toml`; `package-lock.json` ↔ `uv.lock`; `src/` ↔ `app/`; `src/main.jsx` ↔ `main.py` (punto de entrada).
- 📝 Nota del repo: hoy no hay carpeta `dist/` en `frontend/`, así que `npm run build` aún no se ha ejecutado (o se borró). Está ignorada en `.gitignore` de todos modos.

### 2.6 Paso 2 — `SongList` (~40 min)

**Enunciado:** crear `src/SongList.jsx`; al montarse pide `GET /songs` y muestra **cuatro estados**: cargando, error, vacío y la lista.

#### Esqueleto que dio el tutor (con tres huecos)

```jsx
import { useEffect, useState } from "react";

const API = "http://localhost:8000";

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function SongList() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const res = await fetch(`${API}/songs`, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${...}`);       // fetch NO lanza error en un 404 o 500
        setSongs(await res.json());
        setLoading(false);
      } catch (err) {
        if (err.name === "AbortError") return;
        setError(err.message);
        setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [...]);                                                 // ¿cuándo debe ejecutarse el efecto?

  if (loading) return <p>Cargando…</p>;
  if (error) return <p role="alert">Error: {error}</p>;
  if (songs.length === 0) return <p>No hay canciones.</p>;

  return (
    <ul>
      {songs.map((song) => (
        <li key={...}>
          <strong>{song.title}</strong> — {song.artists.map((a) => a.name).join(", ")} ·{" "}
          {song.genre.name} · {formatDuration(song.duration_s)}
        </li>
      ))}
    </ul>
  );
}
```

Y reemplazar `src/App.jsx` por:

```jsx
import SongList from "./SongList";

export default function App() {
  return (
    <main>
      <h1>Music</h1>
      <SongList />
    </main>
  );
}
```

#### Los tres huecos (respuestas del tutor)

| Hueco | Respuesta | Razón |
|---|---|---|
| `` `HTTP ${...}` `` | `res.status` | El número del código HTTP (404, 500…). |
| `}, [...]);` | `[]` | Lista vacía = "solo al montarse". Sin ella el efecto se repetiría en cada render. |
| `<li key={...}>` | `song.id` | React necesita un identificador **estable y único** por elemento para saber qué cambió. El id de la canción, no la posición. |

Versión con los huecos rellenados (según lo indicado por el tutor):

```jsx
if (!res.ok) throw new Error(`HTTP ${res.status}`);
// …
}, []);
// …
<li key={song.id}>
```

#### Qué mirar (explicado por el tutor)

- **`res.ok`:** `fetch` solo rechaza la promesa si no hay red. Un 500 llega como respuesta normal, por eso lo compruebas tú.
- **`AbortController`:** cancela la petición si el componente se desmonta. En desarrollo verás la petición **dos veces** porque React ejecuta los efectos doble a propósito (StrictMode); es normal, y por eso el `AbortError` se ignora (`if (err.name === "AbortError") return;`).
- **Los 4 estados** (cargando, error, vacío, datos) son lo que un entrevistador espera ver **siempre** que haya un `fetch`.

#### Comprobación (los 3 chequeos)

Con los dos servidores levantados, abre `http://localhost:5173`:

1. Deben aparecer las canciones con artistas, género y duración (ej. `3:25`). Formato de cada fila: `**Título** — Artista A, Artista B · Género · m:ss`.
2. **Apaga el backend y recarga:** debe salir un mensaje de error, no una pantalla en blanco.
3. En las herramientas del navegador, pestaña **Network**, mira la petición a `/songs`: la respuesta lleva `access-control-allow-origin`. Es tu middleware de CORS funcionando.

Regla de tiempo del tutor: **"si pasas de 40 minutos, pídeme la solución"**.

#### Forma de la respuesta de `GET /songs` (para saber qué pinta React)

`response_model=list[SongsOut]` en el backend:

```python
class SongsArtistOut(BaseModel):
    artist_id: int
    name: str
    role: Literal["main", "featured", "producer", "writer"]

class SongsOut(BaseModel):
    id: int
    title: str
    duration_s: int = Field(gt=0)
    genre: GenreOut          # {id, name, created_at}
    created_at: datetime
    artists: list[SongsArtistOut]
```

Por eso en el componente se usa `song.artists.map((a) => a.name)`, `song.genre.name` y `song.duration_s`.

#### Estado actual (al escribir estas notas)

- `frontend/src/SongList.jsx`: **creado pero vacío (0 bytes)**.
- `frontend/src/App.jsx`: **sigue siendo la plantilla de Vite** (contador "Count is…", logos).
- Falta, por tanto: escribir `SongList`, cambiar `App.jsx`, probar los 3 chequeos y confirmar al tutor.

📝 Ideas opcionales cuando lo termines: `npm run lint` debe pasar (la regla `react-hooks/exhaustive-deps` es la que explica por qué `[]` es correcto: `API` es una constante fuera del componente); y un `finally` podría centralizar `setLoading(false)` (cuidado con el caso `AbortError`).

### 2.7 Chuleta de comandos de esta lección

```bash
# --- backend (carpeta backend/) ---
uv run pytest tests/test_cors.py -q            # 4 passed
uv run pytest -q                                # 153 passed, 1 skipped (con pandas/NumPy)
uvx ruff check --select F,E9 app tests          # ruff limpio
uv add pandas numpy                             # arregla los errores de colección (lección 8)
uv run uvicorn app.main:app --reload            # API en :8000

# --- frontend (carpeta frontend/) ---
node -v                                         # Node >= 20
npm create vite@latest . -- --template react    # plantilla (carpeta no vacía → Ignore files and continue; ESLint)
npm install                                     # crea node_modules/
npm run dev                                     # Vite en :5173
npm run lint                                    # ESLint
npm run build                                   # genera dist/ (estáticos para producción)
```

📝 Para probar el preflight a mano con `curl` (no se ejecutó en clase; `curl` no aplica CORS, pero te deja ver las cabeceras que devuelve el middleware):

```bash
curl -i -X OPTIONS http://localhost:8000/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization"
# esperable: 200 con access-control-allow-origin: http://localhost:5173
#            access-control-allow-methods (lista de métodos), access-control-allow-headers (los pedidos)
```

## 3. Conceptos enseñados

### 3.1 CORS (Cross-Origin Resource Sharing)

**Origen** = protocolo + host + puerto. Tu React (`http://localhost:5173`) y tu API (`http://localhost:8000`) son **orígenes distintos** (cambia el puerto). Por seguridad, el navegador deja que React *envíe* la petición, pero **no le deja leer la respuesta** salvo que la API lo autorice con cabeceras especiales. Eso es CORS.

Puntos clave que explicó el tutor:

- **Es una regla del navegador.** `curl`, Postman y `pytest` no la aplican; por eso tu API funcionó en todos los tests sin nada de esto, y por eso hubo que simular el navegador mandando la cabecera `Origin` a mano.
- **`add_middleware(CORSMiddleware, ...)`** envuelve **toda** la app con ese código. Se ejecuta en cada petición, antes y después de tus rutas, sin que ninguna ruta lo pida. Es la diferencia con `Depends`, que se aplica endpoint por endpoint.
- **`allow_origins=["http://localhost:5173"]`** — lista de webs autorizadas; aquí solo tu front. `"*"` significaría "cualquiera".
- **`allow_methods=["*"]`** — métodos HTTP que ese JavaScript puede usar (GET, POST, DELETE…). Sin esto solo se permiten los "simples".
- **`allow_headers=["*"]`** — cabeceras que puede enviar. Importan `Authorization` (tu token) y `Content-Type: application/json`.

#### El preflight, paso a paso

Cuando React hace `POST /auth/login` con JSON, el navegador primero manda una consulta previa:

```
OPTIONS /auth/login
Origin: http://localhost:5173
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

El middleware la contesta **él solo, sin llegar a tus rutas**:

```
200
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: ...
Access-Control-Allow-Headers: ...
```

Entonces el navegador envía el `POST` real. Esa respuesta también lleva `Access-Control-Allow-Origin`, y solo así deja que React la lea. Los 4 tests de `test_cors.py` comprueban cada una de estas piezas.

| Cabecera | Quién la manda | Significado |
|---|---|---|
| `Origin` | navegador | desde qué web se hace la petición |
| `Access-Control-Request-Method` / `-Headers` | navegador (solo preflight) | "¿puedo usar este método / estas cabeceras?" |
| `Access-Control-Allow-Origin` | API | "este origen puede leer la respuesta" |
| `Access-Control-Allow-Methods` / `-Headers` | API (preflight) | métodos y cabeceras autorizados |

📝 Ampliación (estándar, no dicho en clase con estas palabras): el preflight solo ocurre en peticiones "no simples": métodos distintos de GET/HEAD/POST, o cabeceras como `Authorization`, o `Content-Type: application/json`. Un `GET /songs` sin cabeceras especiales viaja directamente, sin `OPTIONS` previo — pero igual necesita `Access-Control-Allow-Origin` en la respuesta para que React la lea.

#### Matices de `"*"` (respuesta a tu pregunta del asterisco)

1. **Es un permiso del navegador, no de la API.** `["*"]` no crea rutas ni salta la autenticación. Si React hace `DELETE /playlists/1` sin token, sigues devolviendo **401** como siempre. CORS solo decide si el navegador deja o no hacer la llamada.
2. **Con `Authorization` hay un detalle.** La especificación del navegador dice que un `*` literal **no cubre** esa cabecera y que debe nombrarse explícitamente. **Starlette** (el motor de FastAPI) lo resuelve devolviendo las **cabeceras exactas que el navegador pidió en el preflight**, así que tu login funciona. Si algún día lo haces con otro servidor, comprueba que `Authorization` esté listada.
3. **En producción conviene ser explícito** (principio de mínimo privilegio, y queda más claro para quien lo lea):

```python
allow_methods=["GET", "POST", "DELETE"],
allow_headers=["Authorization", "Content-Type"],
```

Para desarrollo local `["*"]` está bien. En la entrevista puedes decir que usaste `*` por comodidad y que en producción lo restringirías junto con el origen.

#### Para la entrevista (lo que dijo el tutor)

- **CORS protege al usuario, no a tu API.** Un atacante con `curl` no se ve afectado, así que la autenticación sigue siendo necesaria.
- **`"*"` en `allow_origins` solo en APIs públicas sin credenciales.** No se puede combinar con `allow_credentials=True` (cookies). Tu API usa `Bearer` en una cabecera, así que `allow_credentials` no hace falta.
- **En producción el origen sale de una variable de entorno**, no de una cadena fija en el código. (Hoy `allow_origins` está fijo en `main.py` y `app/config.py` no tiene un ajuste de CORS: sería un pequeño cambio futuro, relacionado con [[lesson-7]].)
- **El error también debe llevar la cabecera CORS:** si el `401` no la lleva, el navegador lo oculta y React ve "Network Error" sin saber que era un 401 (de ahí el tercer test).

### 3.2 JavaScript, Node.js, npm, Vite y React: cómo encajan

JavaScript es el lenguaje, Node.js es el programa que lo ejecuta fuera del navegador y React es una librería escrita en JavaScript para construir interfaces.

| Pieza | Qué es | Equivalente en Python |
|---|---|---|
| **JavaScript** | el lenguaje | Python |
| **Node.js** | el entorno que ejecuta JavaScript fuera del navegador | el intérprete `python` |
| **npm** | gestor de paquetes que viene con Node | `pip` / `uv` |
| **Vite** | herramienta de desarrollo: servidor local y empaquetado | `uvicorn --reload` + una herramienta de build |
| **React** | librería para construir interfaces con componentes | una librería como FastAPI o Pydantic: código que usas, no un lenguaje |

**La relación.** JavaScript nació para ejecutarse **solo dentro del navegador**. Node.js sacó ese motor del navegador para correr JavaScript en tu computador, igual que `python archivo.py`; con eso se hicieron herramientas y servidores. React, en cambio, no tiene nada que ver con servidores: es código JavaScript que se ejecuta **en el navegador** y dibuja la pantalla.

**Lo que pasa en tu proyecto:**

```
npm run dev
   └─ Node.js ejecuta Vite ──► sirve tus archivos en localhost:5173
                                   │
                                   ▼
                           el NAVEGADOR descarga y ejecuta tu código React
                                   │  fetch("http://localhost:8000/songs")
                                   ▼
                           uvicorn (Python) ejecuta tu FastAPI
```

Por eso hay **dos servidores**: Node (vía Vite) entrega la página y Python entrega los datos. Node solo hace de herramienta durante el desarrollo. Cuando despliegues, `npm run build` genera archivos estáticos (HTML, CSS y JS) y ya **no necesitas Node en ejecución**. La excepción son frameworks como **Next.js**, que renderizan en el servidor.

**Para la entrevista:**

- React **no es un lenguaje ni un framework completo**: es una librería de interfaces. No trae rutas ni peticiones HTTP, y por eso usas `fetch` aparte.
- Los componentes de React son **funciones de JavaScript** que devuelven **JSX** (HTML dentro del código). Vite traduce el JSX a JavaScript normal antes de que el navegador lo vea.
- Frase para recordar: *"React corre en el navegador; Node lo uso para el tooling."*

### 3.3 React: la idea central

- **UI = f(estado).** La interfaz es una función del estado. Cuando el estado cambia (por ejemplo, llega la lista de canciones), React vuelve a ejecutar la función del componente y actualiza **solo lo que cambió** en la pantalla.
- **Componente** = función de JavaScript que devuelve JSX. Se usa como una etiqueta: `<SongList />`.
- **JSX** = HTML escrito dentro del JavaScript (con `{...}` para meter expresiones). No existe una plantilla HTML aparte: tu matiz de "HTML como template" se corrigió así.
- **Punto de entrada:** `index.html` → `main.jsx` → `<App />`.

### 3.4 Los conceptos de `SongList`

#### `useState`

`const [songs, setSongs] = useState([])` — crea una variable de **estado** con valor inicial `[]` y su función para cambiarla. Cambiarla con `setSongs(...)` provoca un nuevo render. Aquí hay tres estados: `songs` (datos), `loading` (empieza en `true`) y `error` (empieza en `null`).

#### `useEffect` y el arreglo de dependencias

`useEffect(() => { … }, [])` ejecuta código **después de pintar** (efectos secundarios: peticiones, suscripciones…).

- El segundo argumento decide **cuándo**: `[]` = solo al montarse; `[query]` = al montarse y cada vez que `query` cambia; sin arreglo = en cada render (casi siempre un error).
- La función que devuelve el efecto es la **limpieza** (`return () => controller.abort()`): se ejecuta al desmontar (o antes de re-ejecutar el efecto).
- Aquí `[]` es correcto porque el efecto solo usa `API`, una constante fuera del componente.

#### `fetch` y `res.ok`

`fetch(url)` devuelve una promesa que **solo se rechaza si no hay red** (CORS bloqueado también aparece como rechazo). Un 404 o un 500 llegan como respuesta "normal". Por eso:

```js
if (!res.ok) throw new Error(`HTTP ${res.status}`);
```

`res.ok` es `true` para 200–299. `res.status` es el número. `await res.json()` parsea el cuerpo.

#### `async/await` dentro de un efecto

El callback de `useEffect` **no puede ser `async`** directamente (devolvería una promesa en vez de la función de limpieza). Por eso se define `async function load()` dentro y se llama `load()`.

#### `AbortController`

Permite cancelar un `fetch`: se le pasa `{ signal: controller.signal }` y en la limpieza se llama `controller.abort()`. Si la petición se cancela, `fetch` lanza un error con `err.name === "AbortError"`, que se ignora (`return`) porque no es un fallo real.

#### StrictMode (por qué ves la petición dos veces)

`main.jsx` envuelve la app en `<StrictMode>`. En **desarrollo**, React monta → desmonta → vuelve a montar cada componente para detectar efectos sin limpieza. Resultado: `fetch /songs` dos veces en la pestaña Network. Es **normal**, no ocurre en producción, y es justo la razón de ser del `AbortController` y de ignorar `AbortError`.

#### La prop `key`

En una lista (`songs.map(...)`) cada elemento necesita `key` **estable y único** (el `id` de la canción). React la usa para saber qué elemento cambió, se movió o desapareció. Usar el índice del arreglo causa errores sutiles si la lista se reordena o filtra.

#### Los cuatro estados de UI

| Estado | Condición | Qué se pinta |
|---|---|---|
| Cargando | `loading === true` | `<p>Cargando…</p>` |
| Error | `error !== null` | `<p role="alert">Error: …</p>` |
| Vacío | `songs.length === 0` | `<p>No hay canciones.</p>` |
| Datos | el resto | `<ul>` con un `<li key={song.id}>` por canción |

Se resuelven con **retornos tempranos** (`if (loading) return …;`) en ese orden. `role="alert"` hace que los lectores de pantalla anuncien el error. El estado "vacío" depende de que el backend devuelva `200 []` (ver 2.0).

#### Pequeñas piezas de JavaScript usadas

- Plantillas de texto: `` `${API}/songs` `` (equivalente a una f-string).
- `Math.floor(totalSeconds / 60)` y `totalSeconds % 60` para minutos y segundos; `String(n).padStart(2, "0")` para rellenar con ceros (`205` → `"3:25"`; `65` → `"1:05"`).
- `songs.map(fn)` crea un arreglo de elementos JSX; `array.join(", ")` une los nombres de artistas.
- `export default function SongList()` / `import SongList from "./SongList"`: módulos ES (un componente por archivo).

### 3.5 Middleware frente a dependencia (comparación pedida al hilo de CORS)

| | Middleware (`add_middleware`) | Dependencia (`Depends`) |
|---|---|---|
| Alcance | **toda la app**, toda petición | un endpoint o un router concreto |
| Cuándo actúa | antes y después de las rutas, también en errores y en rutas que no existen | dentro del endpoint, después del enrutado |
| Ve la ruta/parámetros ya resueltos | no | sí (inyecta valores) |
| Ejemplos en el proyecto | CORS | `get_db`, `current_user`, `owned_playlist` |

Por eso CORS es middleware: el preflight (`OPTIONS`) se contesta **sin llegar a ninguna ruta**, y debe actuar también en los errores 401/404.

### 3.6 Técnica: tests escritos antes y validados con mutaciones

Patrón de todo el entrenamiento, aplicado también aquí: el tutor valida los tests con una implementación de referencia y luego **rompe el código a propósito** (mutaciones) para comprobar que los tests lo detectan (`allow_origins=["*"]` → 4 fallos; sin `allow_headers` → 1 fallo). Si una mutación sobrevive, el test es demasiado débil.

## 4. Errores cometidos y diagnóstico

| Síntoma / traza | Causa | Arreglo | Lección |
|---|---|---|---|
| `if songs is None or []: raise HTTPException(status_code=200, …)` | `raise` para un caso bueno; `or []` siempre falso; la lista vacía no es un error | Borrar las dos líneas (`return songs`) | Una lista vacía es `200 []`; no se lanza `HTTPException` para éxitos |
| `3 failed, 116 passed` en `test_cors.py`: `assert 405 == 200` y `KeyError: 'access-control-allow-origin'` | Falta `CORSMiddleware`: el `OPTIONS` no existe como ruta (405) y las respuestas no llevan la cabecera | `app.add_middleware(CORSMiddleware, allow_origins=[…], allow_methods=["*"], allow_headers=["*"])` | El preflight lo contesta el middleware, no una ruta |
| `Interrupted: 2 errors during collection` → `ModuleNotFoundError: No module named 'numpy'` / `'pandas'` | Los tests de la lección 8 importan librerías no instaladas; no es fallo de CORS | `uv add pandas numpy` (y commitear `pyproject.toml` + `uv.lock`); mientras tanto `--ignore=` de esos 4 archivos | Un `import` roto en un test aborta la colección entera |
| Duda: "¿qué comando creó `node_modules`, `public`, `src`?" (atribuidas a `npm run build`) | Mezcla de tres comandos distintos | `create vite` → plantilla; `npm install` → `node_modules/`; `npm run build` → `dist/` | Ver tabla de 2.5 |
| Idea: "React orquesta JavaScript y HTML, el HTML es el template" | Matiz: no hay plantilla HTML aparte; el HTML vive dentro del JS como JSX | UI = f(estado); componentes = funciones que devuelven JSX | 3.3 |
| `Current directory is not empty` en `npm create vite` | `frontend/` tenía un `.gitkeep` | "Ignore files and continue" | La plantilla se escribe sobre la carpeta |
| Pregunta de linter (Oxlint vs ESLint) | Decisión de herramienta | ESLint (estándar de la industria) | Elegir lo que verás en la entrevista |

## 5. Cómo se relaciona con el ritme

**Con el README:**

- Cubre el ítem pendiente `- [ ] React: SongList, LoginForm` (se marcará cuando estén `SongList` y `LoginForm`).
- Cumple la parte del stack "React (Vite)" y la futura parte del criterio de "hecho": *"un script con `curl` recorre el flujo completo… y `docker run` levanta la API"* (el front no está en ese criterio, pero sí en el objetivo del proyecto).
- El contrato de la API (tabla de rutas) es exactamente lo que React consume: `GET /songs`, `POST /auth/login`, `GET /me`, rutas de playlists.
- Árbol del README: `backend/ … frontend/` — ahora `frontend/` ya tiene el proyecto Vite.

**Con el resto del proyecto:**

- CORS depende de la [[lesson-4]] (token en `Authorization: Bearer`) y se apoya en el sobre de errores de [[lesson-5]] para que el 401 llegue legible a React.
- El Dockerfile ([[lesson-7]]) tendrá que decidir el origen permitido (variable de entorno) y, en producción, quién sirve el front (`dist/` estático, sin Node).

**Con la entrevista:** la prueba incluye "un componente de React en vivo" y "preguntas básicas de backend/frontend". Lo practicado aquí es el esqueleto de cualquier componente de datos: estado + efecto + `fetch` + los 4 estados + `key`.

## 6. Preguntas de entrevista

1. **¿Qué es CORS y qué problema resuelve?** Una política del navegador: una página de un origen no puede leer respuestas de otro origen salvo que el servidor lo autorice con cabeceras `Access-Control-*`. Protege al usuario, no al servidor.
2. **¿Qué es un preflight?** Un `OPTIONS` automático que el navegador envía antes de peticiones "no simples" (JSON, `Authorization`, métodos como DELETE) para preguntar si están permitidas. En FastAPI lo contesta `CORSMiddleware` sin llegar a las rutas.
3. **¿Protege CORS a tu API?** No. `curl` o un script lo ignoran. La autenticación sigue siendo necesaria.
4. **¿Por qué no `allow_origins=["*"]` siempre?** Autoriza a cualquier web; no se puede combinar con credenciales (`allow_credentials=True`); solo se justifica en APIs públicas sin credenciales. En producción: lista explícita desde una variable de entorno.
5. **¿Diferencia entre middleware y `Depends`?** Middleware envuelve toda la app (CORS, logging); `Depends` se aplica por endpoint e inyecta valores (sesión, usuario).
6. **¿Cómo pruebas CORS sin navegador?** Con `TestClient` enviando la cabecera `Origin` (y `Access-Control-Request-*` para el preflight) y comprobando las cabeceras `Access-Control-*` de la respuesta.
7. **¿Por qué las respuestas de error también deben llevar la cabecera CORS?** Si no, el navegador oculta el 401 y el front solo ve "Network Error".
8. **¿Qué diferencia hay entre JavaScript, Node.js y React?** Lenguaje, entorno de ejecución fuera del navegador, y librería de UI que corre en el navegador.
9. **¿Qué hace `useEffect(() => {…}, [])`? ¿Y si quito el `[]`?** Ejecuta el efecto una vez al montar; sin el arreglo se ejecuta tras cada render (con un `fetch` + `setState` sería un bucle de peticiones).
10. **¿Por qué `res.ok`?** `fetch` solo rechaza ante fallos de red; los 4xx/5xx llegan como respuesta normal y hay que comprobarlos.
11. **¿Para qué el `AbortController`? ¿Por qué veo dos peticiones en desarrollo?** Cancela la petición al desmontar (evita actualizar estado de un componente que ya no existe); StrictMode monta dos veces en desarrollo.
12. **¿Para qué sirve `key` y por qué no el índice?** Identifica elementos entre renders para reconciliar eficientemente; con índices, reordenar/filtrar puede asignar estado al elemento equivocado.
13. **¿Qué estados debe manejar un componente que carga datos?** Cargando, error, vacío y datos.
14. **¿Qué despliegas de un front con Vite?** El contenido de `dist/` (HTML, CSS, JS estáticos); Node no hace falta en producción.

## 7. Qué falta del tutorial de React (hoja de ruta — PENDIENTE, no enseñado todavía)

> Esta sección es un **plan**, no historia de clase. Las respuestas concretas las dará el tutor paso a paso; aquí quedan los conceptos y el contrato de la API que cada paso usará.

### Paso 2 (en curso): terminar `SongList`
- [ ] Escribir `src/SongList.jsx` (hoy vacío) con los tres huecos resueltos.
- [ ] Sustituir `src/App.jsx` por el componente `App` con `<SongList />`.
- [ ] Los 3 chequeos: lista con artistas/género/duración, mensaje de error al apagar el backend, cabecera `access-control-allow-origin` en Network.
- [ ] `npm run lint` sin errores.

### Paso 3 (~20 min): búsqueda con `q` — input controlado
- Concepto: **input controlado** (`value={query}` + `onChange` que llama a `setQuery`): React es la fuente de verdad del texto.
- La URL pasa a `GET /songs?q=<texto>`; el efecto de `SongList` tendrá dependencia **`[query]`** en vez de `[]`, y la limpieza con `AbortController` evita que una respuesta lenta pise a una más reciente (condición de carrera).
- Codificar el texto con `encodeURIComponent` (o `URLSearchParams`). Opcional: *debounce*.
- El backend ya lo soporta: `GET /songs` acepta `q`, `genre_id`, `artist_id`, `limit`, `offset`.

### Paso 4 (~40 min): `LoginForm` y guardar el token
- Formulario controlado (email, contraseña); `onSubmit` con `event.preventDefault()`.
- Llamada: `POST /auth/login` con cuerpo **JSON** `{"email": …, "password": …}` (el esquema `UserCreate`, no un formulario OAuth2) y cabecera `Content-Type: application/json` → esto es lo que dispara el **preflight** que ya cubre tu middleware.
- Respuesta correcta: `200 {"access_token": "...", "token_type": "bearer"}`. Error: `401` con el sobre `{"error": {"code": "unauthorized", "message": "Invalid email or password"}}`.
- **Dónde guardar el token (decisión que se tomará en esa lección; riesgos):**
  - *Memoria (estado de React):* no es accesible desde otras pestañas ni persiste; se pierde al recargar. Menos expuesto a robo por XSS.
  - *`localStorage`:* persiste y es lo más simple, pero **cualquier JavaScript de la página lo lee**: un XSS roba el token.
  - *Cookie `HttpOnly`:* JavaScript no puede leerla, pero obliga a cambiar el backend (`allow_credentials=True` con origen explícito, `SameSite`, protección CSRF).
- Recuerda que el token del backend caduca (`access_token_minutes = 60`).

### Paso 5 (~20 min): llamada autenticada con `Bearer`
- Enviar `Authorization: Bearer <token>` en cada petición protegida: `GET /me` (devuelve `UserOut`) o `GET /playlists` (las del usuario).
- Manejar el **401** (sin token, token inválido o expirado): volver al login.
- Logout: borrar el token en el cliente. El `DELETE /auth/logout` del backend sigue siendo un stub `501` (JWT sin estado: no hay nada que invalidar en el servidor).
- Probar que el navegador envía el preflight con `authorization` y que el middleware lo permite.

### Después de React
- Marcar `React: SongList, LoginForm` en el README y commitear (`frontend/` incluye `package.json` y `package-lock.json`; `node_modules/` y `dist/` ya están ignorados).
- Diseño del sistema de streaming (subida → almacenamiento → transcodificación → CDN → ABR/HLS), narrativa de experiencia y simulacro de 90 minutos; Dockerfile ([[lesson-7]]) si hay tiempo.

## 8. Checklist / estado

- [x] Tests de CORS escritos y validados (4 tests, 2 mutaciones)
- [x] `CORSMiddleware` añadido en `app/main.py` (`test_cors.py`: 4 passed)
- [x] Entendido: origen, preflight, middleware vs `Depends`, `"*"`, CORS protege al navegador
- [x] Suite del backend completa: 153 passed, 1 skipped
- [x] Proyecto Vite creado (React + ESLint) y `npm run dev` verificado junto con la API
- [x] Entendido: JS vs Node vs npm vs Vite vs React; qué crea cada comando
- [ ] Borrar del todo las dos líneas comentadas en `list_songs`
- [ ] Escribir `SongList.jsx` y cambiar `App.jsx` (Paso 2)
- [ ] Búsqueda con `q` (Paso 3)
- [ ] `LoginForm` + token (Paso 4)
- [ ] Llamada autenticada con Bearer (Paso 5)
- [ ] Marcar `React: SongList, LoginForm` en el README
- [ ] **Profundizar en middlewares** (tema aplazado a petición tuya): orden de ejecución de varios middlewares, escribir uno propio (tiempos/logs), `BaseHTTPMiddleware` frente a ASGI puro, y cómo interactúan con los manejadores de excepciones
- [ ] Pasar el origen permitido de CORS a una variable de entorno (lo ideal antes del Dockerfile)

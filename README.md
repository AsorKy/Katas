# Katas

Práctica deliberada de programación **a mano**: katas de Python, un proyecto full stack construido paso a paso y diseños de arquitectura backend.

## Para qué sirve este repositorio

- **Mantener la fluidez escribiendo código a mano**, sin depender del autocompletado ni de código generado.
- **Entrenar el stack de un backend en Python:** estructuras de datos, FastAPI, SQL, autenticación, contenedores.
- **Practicar diseño de sistemas:** pensar y explicar arquitecturas backend (componentes, flujo de datos, decisiones y sus compromisos).
- **Dejar evidencia:** cada ejercicio se valida con `assert` o con tests, y cada sesión larga queda registrada en notas de clase.

## Contenido

| Carpeta | Qué hay | Estado |
|---|---|---|
| [`python-backend/python-basics/`](python-backend/python-basics/) | 5 katas de Python con `assert` y un notebook de pruebas | 5 katas |
| [`fullstack-project-music/`](fullstack-project-music/) | Music API: backend FastAPI, frontend React y Docker Compose, con notas de clase y diagramas | completo |
| Diseño de arquitectura backend | Casos de diseño por escrito; el primero, una plataforma de streaming en la nube | por añadir |
| [`node-react/`](node-react/) | Repaso exprés de Node y React: fichas de memoria, recetas de código y retos con pruebas | en curso |

### `python-backend/python-basics/`

Ejercicios cortos y autocontenidos, sin dependencias externas. Cada uno termina con `assert`: un kata está resuelto cuando se ejecuta sin `AssertionError`.

| Kata | Tema |
|---|---|
| `01-parse-text.py` | Parsear líneas de texto `marca-de-tiempo clave=valor …` en un diccionario |
| `02-list-split-unfold.py` | Listas: slicing, división y desempaquetado |
| `03-dictionaries.py` | Diccionarios: contar y agrupar |
| `04-nested-data-&-reconstruction.py` | Datos anidados: aplanar y reconstruir con recursión |
| `05-sort-composed-keys.py` | Ordenar con claves compuestas |

`tests.ipynb` es un cuaderno de pruebas con las exploraciones de las expresiones que se usan en los katas.

```bash
python python-backend/python-basics/02-list-split-unfold.py
python "python-backend/python-basics/04-nested-data-&-reconstruction.py"   # el & obliga a usar comillas
```

### `fullstack-project-music/`

API de música (usuarios, artistas, canciones, géneros y playlists) con **contrato primero**: se define y se prueba la interfaz antes de implementarla.

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (síncrono), SQLite, JWT con Argon2, pandas y NumPy en dos endpoints de análisis, pytest y uv.
- **Frontend:** React con Vite (listado con búsqueda, login y sesión con token).
- **Despliegue:** un Dockerfile por servicio y `docker compose` para levantar todo con un comando.
- **Documentación:** su propio [README](fullstack-project-music/README.md) (alcance, modelo de datos, contrato completo de la API) y nueve notas de clase en [`tutorial-docs/`](fullstack-project-music/tutorial-docs/) con diagramas SVG.

Levantarlo (requiere Docker):

```bash
cd fullstack-project-music
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
docker compose up --build
```

La API queda en `http://localhost:8000/docs` y la interfaz en `http://localhost:5173`. Con la app levantada, `./scripts/smoke.sh` recorre el flujo completo con `curl`. Para ejecutar solo los tests:

```bash
cd fullstack-project-music/backend
uv sync
uv run pytest -q
```

Notas de clase, en el orden en que se construyó el proyecto:

| Nota | Tema |
|---|---|
| [lección 1](fullstack-project-music/tutorial-docs/lesson-1.md) | Entorno: git, uv, dependencias, pytest y `/health` |
| [lección 2](fullstack-project-music/tutorial-docs/lesson-2.md) | Contrato de la API: tabla de rutas, stubs 501 y tests de contrato |
| [lección 3](fullstack-project-music/tutorial-docs/lesson-3.md) | Modelos SQLAlchemy, base SQLite y semilla |
| [lección 4](fullstack-project-music/tutorial-docs/lesson-4.md) | Autenticación: Argon2, JWT, registro, login y `/me` |
| [lección 5](fullstack-project-music/tutorial-docs/lesson-5.md) | Canciones y artistas con SQL, errores uniformes y capa de servicio |
| [lección 6](fullstack-project-music/tutorial-docs/lesson-6.md) | Playlists: dueño, 404 frente a 403, posición y conflictos |
| [lección 7](fullstack-project-music/tutorial-docs/lesson-7.md) | Docker: backend, frontend y Compose |
| [lección 8](fullstack-project-music/tutorial-docs/lesson-8.md) | pandas y NumPy: estadísticas por género y canciones similares |
| [lección 9](fullstack-project-music/tutorial-docs/lesson-9.md) | CORS y React: Node, Vite, componentes y estado |

## Método de trabajo

1. **El enunciado o el contrato primero.** Qué tiene que hacer, antes de cómo.
2. **Los tests antes que el código.** `assert` en las katas, pytest en los proyectos.
3. **El código se escribe a mano.** Las especificaciones, los tests y las revisiones se preparan con ayuda de un tutor de IA (Claude); la implementación y los commits son propios.
4. **Los errores se diagnostican y se anotan.** Cada nota de clase incluye una tabla de síntoma, causa y arreglo.
5. **Cada sesión deja una nota.** Qué se hizo, qué conceptos aparecieron, qué se rompió y qué preguntas de entrevista se desprenden.

## Convenciones

- **Katas:** archivos numerados `NN-tema.py`, autocontenidos y verificables con `assert`.
- **Proyectos:** carpeta propia con su README (alcance, contrato, cómo ejecutarlo), tests y notas de clase.
- **Diseños de arquitectura:** una carpeta por caso con su README. Estructura prevista: requisitos y supuestos, componentes, flujo de datos, decisiones con sus compromisos y qué cambia al escalar.
- **Secretos:** viven en `.env`, ignorado por git; nunca se escriben en el código ni en las imágenes.

## Hoja de ruta

- [x] Katas de Python básico (5)
- [x] Proyecto full stack: API, base de datos, autenticación, análisis, frontend y Docker Compose
- [ ] Diseño de arquitectura backend: plataforma de streaming (almacenamiento, entrega, metadatos, escalado)
- [ ] Más katas a mano, orientadas a backend

---
tags: [fullstack-project-music, leccion, pendiente]
leccion: 7
estado: pendiente
---

# Lección 7 · Dockerfile (pendiente)

> **Estado:** todavía no la hemos hecho. Esta nota recoge lo que ya está acordado en el README y en el plan de entrenamiento, para que cuando llegues a ella sepas exactamente qué se espera. Lo que sigue no es historia de clase: es el punto de partida.

## 0. Dónde encaja

- Es el **séptimo y último paso de construcción** del proyecto (entorno → contrato → modelos → autenticación → canciones y artistas → playlists → **Dockerfile**).
- En el plan de entrenamiento es lo **primero que se recorta** si falta tiempo. El orden de recortes acordado fue: **Dockerfile → pandas/NumPy → playlists**. Playlists y pandas/NumPy ya se hicieron; el Dockerfile sigue pendiente.
- Aparece en el README como último ítem del checklist (`- [ ] Dockerfile`).

## 1. Qué dice el README (la especificación)

Del README del proyecto:

- **Stack:** "…React (Vite) · un solo Dockerfile al final."
- **Fuera de alcance (por ahora):** "subida de audio real, Redis, Alembic, **Compose**, pagos". Es decir: **un único Dockerfile, sin Docker Compose**.
- **Configuración:** "La URL de la base sale de la variable `DATABASE_URL`, así que pasar a Postgres es cambiar una línea." Esto ya está resuelto en el código con `pydantic-settings` (`Settings.database_url`), así que el contenedor se configura por variable de entorno, no editando código.
- **Criterio de "hecho"** (sección del README): "Los tests pasan, `/docs` muestra el contrato, un script con `curl` recorre el flujo completo (registro, login, crear canción, crear playlist, añadir canción) y **`docker run` levanta la API**."

## 2. Lo que ya tienes preparado para esta lección

| Pieza | Dónde | Por qué importa para el contenedor |
|---|---|---|
| Dependencias declaradas | `backend/pyproject.toml` y `backend/uv.lock` | Se instalan en la imagen con `uv`, sin adivinar versiones |
| Versión de Python fijada | `.python-version` (3.12) | La imagen base debe ser Python 3.12 |
| Configuración por entorno | `app/config.py` (`Settings`) | `DATABASE_URL` y `SECRET_KEY` se pasan con `-e` / `--env-file` |
| Servidor de arranque | `uv run uvicorn app.main:app` | Es el comando que acabará en el `CMD` |
| `.gitignore` | raíz del repo | Lo que ahí se ignora (`.venv/`, `__pycache__/`, `*.db`, `.env`) tampoco debe entrar en la imagen: se repite en un `.dockerignore` |
| Base SQLite y semilla | `backend/data/` | Decidir si la base vive dentro del contenedor (efímera) o en un volumen |

## 3. Qué tendremos que decidir y aprender (guion)

1. **Imagen base:** `python:3.12-slim` frente a otras, y por qué `slim`.
2. **Instalar con `uv` dentro de la imagen** y aprovechar la caché de capas: copiar primero `pyproject.toml` + `uv.lock`, instalar, y después copiar el código. Así un cambio en el código no reinstala todas las dependencias.
3. **`.dockerignore`:** qué excluir (`.venv`, caches, bases `.db`, `.env`, tests si no se necesitan).
4. **Secretos:** la `secret_key` de desarrollo que hay por defecto en `config.py` **no** debe llegar a producción; se inyecta como variable de entorno al ejecutar, nunca se hornea en la imagen.
5. **Comando de arranque:** `uvicorn` escuchando en `0.0.0.0` (no `127.0.0.1`, o el puerto publicado no respondería desde fuera del contenedor).
6. **Persistencia de SQLite:** un volumen para `data/` frente a base efímera; y por qué en producción se cambiaría a Postgres con solo cambiar `DATABASE_URL`.
7. **Verificación:** `docker build` → `docker run -p 8000:8000 …` → `curl localhost:8000/health` → recorrer el flujo completo con el script de `curl` del criterio de "hecho".

## 4. Para la entrevista (lo que conviene poder decir)

- Qué es una imagen frente a un contenedor, y qué es una capa.
- Por qué el orden de las instrucciones del Dockerfile importa para la caché.
- Por qué la configuración va por variables de entorno (factor III de los *12-factor apps*) y no dentro de la imagen.
- Por qué no se mete la base de datos de producción dentro del contenedor de la API.

## 5. Checklist

- [ ] Escribir el `Dockerfile` del backend
- [ ] Escribir el `.dockerignore`
- [ ] `docker build` sin errores
- [ ] `docker run` levanta la API y `/health` responde
- [ ] El flujo completo con `curl` funciona contra el contenedor
- [ ] Marcar `Dockerfile` en el checklist del README

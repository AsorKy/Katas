FROM python:3.12-slim 

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:$PATH" \
    DATABASE_URL=sqlite:////db/music.db 

WORKDIR /app

# archivos que definen las dependencias
COPY pyproject.toml uv.lock ./

# instalacion del lock
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY data/seed.json ./data/seed.json

RUN mkdir -p /db

EXPOSE 8000

# el host que escucha en todas las interfases
CMD ["sh", "-c", "python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

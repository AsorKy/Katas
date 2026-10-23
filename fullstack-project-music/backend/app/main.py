from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import genres
from app.routers import artists
from app.routers import songs
from app.routers import playlists
from app.routers import auth
from app.routers import users


app = FastAPI(title="Music-api")

app.include_router(genres.router)
app.include_router(artists.router)
app.include_router(songs.router)
app.include_router(playlists.router)
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/health")
def health():
    return {"status": "ok"}

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
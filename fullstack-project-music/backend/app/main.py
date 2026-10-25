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
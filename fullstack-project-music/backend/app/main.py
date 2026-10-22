from fastapi import FastAPI
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
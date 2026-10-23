import json
from pathlib import Path

from sqlalchemy import func, select

from app import models
from app.db import Base, SessionLocal, engine

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.json"


def flatten_catalog(catalog: dict) -> dict:
    rows = {"genres": [], "artists": [], "songs": [], "song_artists": []}
    genre_ids, artist_ids = {}, {}

    def ensure(name, ids, table):
        if name not in ids:
            ids[name] = len(ids) + 1
            table.append({"id": ids[name], "name":name})
        return ids[name]


    for artist in catalog["artists"]:
        artist_id = ensure(artist["name"], artist_ids, rows["artists"])
        for song in artist["songs"]:
            genre_id = ensure(song["genre"], genre_ids, rows["genres"])
            song_id = len(rows["songs"]) + 1
            rows["songs"].append({"id": song_id, "title": song["title"], "duration_s": song["duration_s"], "genre_id": genre_id})
            rows["song_artists"].append({"song_id": song_id, "artist_id": artist_id, "role": "main"})

            for name in song.get("featuring", []):
                feat_id = ensure(name, artist_ids, rows["artists"])
                rows["song_artists"].append({"song_id": song_id, "artist_id": feat_id, "role": "featured"})
    
    return rows


def seed_database(session, catalog: dict) -> bool:
    """Carga el catálogo en la base. Devuelve False si ya estaba sembrada."""
    if session.scalar(select(func.count()).select_from(models.Song)) > 0:
        return False

    rows = flatten_catalog(catalog)
    session.add_all([models.Genre(**r) for r in rows["genres"]])
    session.add_all([models.Artist(**r) for r in rows["artists"]])
    session.add_all([models.Song(**r) for r in rows["songs"]])
    session.add_all([models.SongArtist(**r) for r in rows["song_artists"]])
    session.commit()
    return True


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    catalog = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    with SessionLocal() as session:
        print("sembrada" if seed_database(session, catalog) else "ya estaba sembrada")

import numpy as np
from sqlalchemy.orm import Session

from app.repositories import songs as songs_repo


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



def similar_songs(db: Session, song_id: int, limit: int) -> list[dict]:
    rows = songs_repo.list_song_rows(db)
    links = songs_repo.list_song_artist_links(db)
    matrix = feature_matrix(
        [(sid, gid) for sid, _, gid in rows], 
        links
    )
    row_of = {sid: i for i , (sid, _, _) in enumerate(rows)}
    target = row_of[song_id]
    return [
        {"song_id": rows[i][0], "title": rows[i][1], "score": round(score, 4)}
        for i, score in top_similar(matrix=matrix, target=target, limit=limit)
    ]
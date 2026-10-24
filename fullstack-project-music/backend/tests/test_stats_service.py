"""pandas: agregación por género (función pura sobre un DataFrame, sin base de datos)."""
import pandas as pd

from app.services.stats import top_genres

COLS = ["genre_id", "name", "song_id", "duration_s", "playlist_id"]


def frame(*rows):
    """Una fila por (género, canción, playlist). Lo que un LEFT JOIN no encuentra llega como None."""
    return pd.DataFrame(list(rows), columns=COLS)


def row(genre_id, name, songs, playlists, avg):
    return {"genre_id": genre_id, "name": name, "song_count": songs,
            "playlist_count": playlists, "avg_duration_s": avg}


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


def test_ranks_by_playlists_then_songs_then_name():
    assert top_genres(frame(*ROWS), limit=10) == [
        row(1, "Rock", 2, 2, 150.0),
        row(4, "Folk", 1, 1, 60.0),      # empata con Pop en playlists y canciones: gana el nombre
        row(2, "Pop", 1, 1, 300.0),
        row(5, "Blues", 0, 0, 0.0),      # géneros sin canciones: aparecen con ceros
        row(3, "Jazz", 0, 0, 0.0),
    ]


def test_avg_duration_counts_each_song_once():
    # la canción 1 (100 s) sale en dos filas porque está en dos playlists:
    # promediar filas daría 133.3 y no 150.0
    r = top_genres(frame((1, "Rock", 1, 100, 1), (1, "Rock", 1, 100, 2), (1, "Rock", 2, 200, 1)), limit=5)
    assert r[0]["avg_duration_s"] == 150.0


def test_avg_duration_is_rounded_to_one_decimal():
    r = top_genres(frame((1, "Rock", 1, 100, None), (1, "Rock", 2, 101, None), (1, "Rock", 3, 101, None)), limit=5)
    assert r[0]["avg_duration_s"] == 100.7


def test_playlist_counted_once_per_genre():
    # dos canciones de Rock en la MISMA playlist cuentan una vez
    r = top_genres(frame((1, "Rock", 1, 100, 7), (1, "Rock", 2, 200, 7)), limit=5)
    assert r[0]["playlist_count"] == 1 and r[0]["song_count"] == 2


def test_limit_applies_after_sorting():
    assert [g["name"] for g in top_genres(frame(*ROWS), limit=2)] == ["Rock", "Folk"]


def test_only_genres_without_songs():
    # columnas enteras de None (dtype object): tampoco debe romperse
    r = top_genres(frame((3, "Jazz", None, None, None), (5, "Blues", None, None, None)), limit=5)
    assert r == [row(5, "Blues", 0, 0, 0.0), row(3, "Jazz", 0, 0, 0.0)]


def test_empty_frame_returns_empty_list():
    assert top_genres(frame(), limit=5) == []


def test_returns_plain_python_types():
    r = top_genres(frame(*ROWS), limit=1)[0]
    assert type(r["genre_id"]) is int and type(r["song_count"]) is int
    assert type(r["playlist_count"]) is int and type(r["avg_duration_s"]) is float


def test_does_not_modify_the_input_frame():
    df = frame(*ROWS)
    before = df.copy()
    top_genres(df, limit=5)
    pd.testing.assert_frame_equal(df, before)

"""NumPy: matriz de características y similitud coseno (funciones puras, sin base de datos)."""
import warnings

import numpy as np
import pytest

from app.services.similarity import feature_matrix, top_similar


# ---------- feature_matrix ----------
def test_feature_matrix_layout():
    songs = [(1, 10), (2, 10), (3, 20)]                 # (song_id, genre_id)
    links = [(1, 7), (1, 8), (2, 7), (3, 9)]            # (song_id, artist_id)
    m = feature_matrix(songs, links)
    # columnas: géneros [10, 20] y después artistas [7, 8, 9], ambos ordenados por id
    assert m.tolist() == [
        [1, 0, 1, 1, 0],
        [1, 0, 1, 0, 0],
        [0, 1, 0, 0, 1],
    ]
    assert m.dtype == np.float64


def test_feature_matrix_empty():
    assert feature_matrix([], []).shape == (0, 0)


def test_feature_matrix_song_without_artists_keeps_its_genre():
    assert feature_matrix([(1, 10)], []).tolist() == [[1]]


# ---------- top_similar ----------
M = np.array([
    [1, 1, 0],      # 0  (objetivo)
    [1, 1, 0],      # 1  idéntica
    [1, 0, 0],      # 2  comparte una de dos
    [0, 0, 1],      # 3  nada en común
    [0, 0, 0],      # 4  vector cero
], dtype=float)
M.setflags(write=False)       # si una función modifica la matriz en el sitio, falla con ValueError


def test_scores_and_order():
    res = top_similar(M, target=0, limit=10)
    assert [i for i, _ in res] == [1, 2]
    assert res[0][1] == pytest.approx(1.0)
    assert res[1][1] == pytest.approx(1 / np.sqrt(2))


def test_excludes_target_and_non_positive_scores():
    assert 0 not in [i for i, _ in top_similar(M, target=0, limit=10)]
    assert [i for i, _ in top_similar(M, target=3, limit=10)] == []


def test_ties_keep_row_order():
    # 40 filas idénticas: todas empatan y deben salir en orden de fila.
    # (con pocas filas un orden no estable podría pasar por casualidad)
    same = np.ones((40, 2))
    assert [i for i, _ in top_similar(same, target=20, limit=100)] == [i for i in range(40) if i != 20]


def test_limit():
    assert [i for i, _ in top_similar(M, target=0, limit=1)] == [1]
    assert len(top_similar(M, target=0, limit=100)) == 2


def test_zero_vectors_do_not_warn_or_produce_nan():
    with warnings.catch_warnings():
        warnings.simplefilter("error")            # cualquier RuntimeWarning rompe el test
        assert top_similar(M, target=4, limit=5) == []          # el objetivo es un vector cero
        res = top_similar(M, target=0, limit=5)                 # hay un vector cero entre los candidatos
    assert all(np.isfinite(s) for _, s in res)


def test_returns_plain_python_numbers():
    for i, s in top_similar(M, target=0, limit=5):
        assert type(i) is int and type(s) is float


def test_does_not_modify_the_matrix():
    m = np.array([[3, 4, 0], [1, 0, 0], [0, 0, 2]], dtype=float)      # normas distintas de 1
    before = m.copy()
    top_similar(m, target=0, limit=5)
    assert (m == before).all()

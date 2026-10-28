"""Reto 1 (15 min) · top_n_palabras

Reglas del drill: a mano, sin IA, sin mirar otros archivos. Cronometra.
Al terminar, escribe como comentario la complejidad de tu solución.
Está resuelto cuando `python 01-top-palabras.py` termina sin AssertionError.
"""


def top_n_palabras(texto: str, n: int) -> list[tuple[str, int]]:
    """Devuelve las n palabras más frecuentes de `texto` como (palabra, veces).

    - Palabra = secuencia de letras o dígitos (Unicode: «canción» es una palabra).
    - No distingue mayúsculas: «La» y «la» son la misma; se devuelve en minúsculas.
    - Orden: más veces primero; a igual número de veces, alfabético ascendente.
    - Si hay menos de n palabras distintas, devuelve todas. Si n <= 0, devuelve [].
    """
    raise NotImplementedError


# --- Pruebas (no las edites) ---
assert top_n_palabras("a b a c b a", 2) == [("a", 3), ("b", 2)]
assert top_n_palabras("La casa, la CASA; la luna.", 3) == [("la", 3), ("casa", 2), ("luna", 1)]
assert top_n_palabras("zeta alfa beta zeta alfa beta", 3) == [("alfa", 2), ("beta", 2), ("zeta", 2)]
assert top_n_palabras("Canción canción CANCIÓN ñandú", 2) == [("canción", 3), ("ñandú", 1)]
assert top_n_palabras("x y", 10) == [("x", 1), ("y", 1)]
assert top_n_palabras("ep1 ep2 ep1", 1) == [("ep1", 2)]
assert top_n_palabras("hola hola", 0) == []
assert top_n_palabras("hola", -3) == []
assert top_n_palabras("", 5) == []
assert top_n_palabras("¡¿...?!", 5) == []
print("Reto 1: OK")

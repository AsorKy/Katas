"""Reto 2 (15 min) · fusionar_intervalos y segundos_escuchados

Contexto: guardas los tramos de una canción que el usuario ya reprodujo, como
(inicio, fin) en segundos, y quieres saber cuánto escuchó de verdad.

Reglas del drill: a mano, sin IA. Cronometra.
Al terminar, escribe como comentario la complejidad de `fusionar_intervalos`.
Está resuelto cuando `python 02-fusionar-intervalos.py` termina sin AssertionError.
"""


def fusionar_intervalos(intervalos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Fusiona los intervalos que se solapan o se tocan (el fin de uno == el inicio de otro).

    - La entrada llega desordenada. NO debes modificarla.
    - La salida es una lista de tuplas ordenada por inicio.
    - Si algún intervalo tiene inicio > fin, lanza ValueError.
    """
    raise NotImplementedError


def segundos_escuchados(intervalos: list[tuple[int, int]]) -> int:
    """Segundos distintos escuchados: suma de las longitudes de los intervalos fusionados."""
    raise NotImplementedError


# --- Pruebas (no las edites) ---
assert fusionar_intervalos([]) == []
assert fusionar_intervalos([(4, 7)]) == [(4, 7)]
assert fusionar_intervalos([(1, 2), (5, 6)]) == [(1, 2), (5, 6)]
assert fusionar_intervalos([(8, 10), (1, 3), (2, 6), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]
assert fusionar_intervalos([(1, 2), (2, 3)]) == [(1, 3)]
assert fusionar_intervalos([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]
assert fusionar_intervalos([(1, 2), (1, 2)]) == [(1, 2)]

entrada = [(8, 10), (1, 3), (2, 6)]
copia = list(entrada)
fusionar_intervalos(entrada)
assert entrada == copia, "no modifiques la entrada"

try:
    fusionar_intervalos([(5, 1)])
except ValueError:
    pass
else:
    raise AssertionError("inicio > fin debe lanzar ValueError")

assert segundos_escuchados([]) == 0
assert segundos_escuchados([(0, 30), (20, 50), (100, 110)]) == 60
assert segundos_escuchados([(0, 10), (10, 20)]) == 20
print("Reto 2: OK")

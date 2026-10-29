// Reto 00 · JS básico para pythonistas (20 min)
//
// Reglas del drill: a mano, sin IA, sin mirar otros archivos. Cronometra.
// Está resuelto cuando `node retos/00-js-basico.js` termina con todos los chequeos en ✔.
// Ficha de apoyo: fichas/00-js-para-pythonistas.md

import assert from "node:assert/strict";
import { chequear, resumen } from "./_util.js";

// ───────────── TU CÓDIGO ─────────────

/** 1. Las n palabras más frecuentes, como [palabra, veces].
 *  Igual que tu kata de Python: minúsculas, Unicode («canción» es UNA palabra),
 *  más veces primero y, si empatan, orden alfabético. Si n <= 0 → [].
 *  Ojo: en JS la expresión regular \w solo entiende ASCII. */
export function topPalabras(texto, n) {
  if (n <= 0) {
    return [];
  }
  
  const palabras = texto.toLowerCase().match(/[\p{L}\p{N}_]+/gu) ?? [];
  const cuenta = new Map(); 
  for (const palabra of palabras) {
    cuenta.set(palabra,  (cuenta.get(palabra) ?? 0) + 1)
  }
  
  const pares = [...cuenta.entries()];
  pares.sort((x,y) => y[1] - x[1] || x[0].localeCompare(y[0]));
  return pares.slice(0,n);
  
};

/** 2. Agrupa objetos por el valor de una clave → { valor: [objetos] }.
 *  (El defaultdict(list) de Python.) */
export function agruparPor(items, clave) {
  const grupos = {}
  for (const item of items){
    const k = item[clave]
    if (!grupos[k]){
      grupos[k] = []
    }
    grupos[k].push(item)
  };
  return grupos
};

/** 3. Devuelve una COPIA ordenada de menor a mayor. No modifica el original. */
export function ordenarNumeros(xs) {
  return [...xs].sort((a,b) => a - b)
};

/** 4. Quita repetidos conservando el orden de la primera aparición. */
export function sinDuplicados(xs) {
  return [...new Set(xs)]
};

/** 5. Devuelve x, salvo que sea null o undefined: entonces devuelve porDefecto.
 *  0, "" y false SON valores válidos y se conservan. */
export function conDefecto(x, porDefecto) {
  return x ?? porDefecto;
}

// ───────────── PRUEBAS (no las edites) ─────────────

await chequear("topPalabras: cuenta y ordena", () => {
  assert.deepEqual(topPalabras("a b a c b a", 2), [["a", 3], ["b", 2]]);
  assert.deepEqual(topPalabras("La casa, la CASA; la luna.", 3), [["la", 3], ["casa", 2], ["luna", 1]]);
});

await chequear("topPalabras: empate → alfabético", () => {
  assert.deepEqual(topPalabras("zeta alfa beta zeta alfa beta", 3), [["alfa", 2], ["beta", 2], ["zeta", 2]]);
});

await chequear("topPalabras: Unicode («canción» es una palabra)", () => {
  assert.deepEqual(topPalabras("Canción canción CANCIÓN ñandú", 2), [["canción", 3], ["ñandú", 1]]);
});

await chequear("topPalabras: dígitos y bordes", () => {
  assert.deepEqual(topPalabras("ep1 ep2 ep1", 1), [["ep1", 2]]);
  assert.deepEqual(topPalabras("x y", 10), [["x", 1], ["y", 1]]);
  assert.deepEqual(topPalabras("hola hola", 0), []);
  assert.deepEqual(topPalabras("hola", -3), []);
  assert.deepEqual(topPalabras("", 5), []);
  assert.deepEqual(topPalabras("¡¿...?!", 5), []);
});

await chequear("agruparPor: agrupa por clave", () => {
  const items = [
    { genero: "rock", titulo: "a" },
    { genero: "pop", titulo: "b" },
    { genero: "rock", titulo: "c" },
  ];
  assert.deepEqual({ ...agruparPor(items, "genero") }, {
    rock: [items[0], items[2]],
    pop: [items[1]],
  });
  assert.deepEqual({ ...agruparPor([], "genero") }, {});
});

await chequear("ordenarNumeros: orden numérico, no de texto", () => {
  assert.deepEqual(ordenarNumeros([10, 2, 1]), [1, 2, 10]);
  assert.deepEqual(ordenarNumeros([3, -1, 2.5]), [-1, 2.5, 3]);
  assert.deepEqual(ordenarNumeros([]), []);
});

await chequear("ordenarNumeros: no modifica el original", () => {
  const original = [10, 2, 1];
  const resultado = ordenarNumeros(original);
  assert.deepEqual(original, [10, 2, 1]);
  assert.notEqual(resultado, original, "debe devolver otro arreglo");
});

await chequear("sinDuplicados: conserva el orden", () => {
  assert.deepEqual(sinDuplicados([3, 1, 3, 2, 1]), [3, 1, 2]);
  assert.deepEqual(sinDuplicados(["a", "a"]), ["a"]);
  assert.deepEqual(sinDuplicados([]), []);
});

await chequear("conDefecto: solo null/undefined usan el valor por defecto", () => {
  assert.equal(conDefecto(null, 5), 5);
  assert.equal(conDefecto(undefined, 5), 5);
  assert.equal(conDefecto(0, 5), 0);
  assert.equal(conDefecto("", "a"), "");
  assert.equal(conDefecto(false, true), false);
  assert.equal(conDefecto("x", "a"), "x");
});

resumen();

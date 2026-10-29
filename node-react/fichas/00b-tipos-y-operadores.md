# 00b · Tipos y operadores: Python ↔ JS

> Complemento de la ficha 00. Primero la traducción; al final, las trampas que más caen.

## Tipos de datos

| Python | JS | Ojo |
|---|---|---|
| `int`, `float` | `number` (un solo tipo, decimal de 64 bits) | `5 / 2` da `2.5`. Los enteros son exactos solo hasta `9007199254740991`; para más, `bigint` (`10n`) |
| `str` | `string` | comillas `'`, `"` o `` ` ``; no se modifica; largo con `.length` |
| `bool` (`True`) | `boolean` (`true`) | minúsculas |
| `None` | `null` y `undefined` | dos «vacíos» distintos |
| `list` | `Array` | `typeof [] === "object"`; para saber si es arreglo: `Array.isArray(x)` |
| `dict` | `Object` o `Map` | las claves de un objeto son texto; `Map` acepta cualquier clave |
| `set` | `Set` | |
| `tuple` | no existe | usa un arreglo |
| `datetime` | `Date` | |
| función | `function` o flecha `=>` | las funciones también son valores |

`type(x)` de Python es `typeof x` en JS:

```js
typeof 5            // "number"
typeof "a"          // "string"
typeof true         // "boolean"
typeof undefined    // "undefined"
typeof null         // "object"    ← bug histórico: para null usa  x === null
typeof []           // "object"    ← usa Array.isArray(x)
typeof (() => 1)    // "function"
typeof NaN          // "number"
```

### Convertir tipos

| Python | JS |
|---|---|
| `int("5")`, `float("5.5")` | `Number("5")` |
| `str(5)` | `String(5)` |
| `bool(x)` | `Boolean(x)` |
| `int("42px")` → error | `parseInt("42px")` → `42` · `Number("42px")` → `NaN` |

## Operadores

### Aritméticos

| Python | JS | Ojo |
|---|---|---|
| `+ - * /` | igual | `/` siempre da decimal, en los dos |
| `//` | `Math.floor(a / b)` | `Math.floor(-7 / 2)` da `-4`, igual que Python; `Math.trunc` daría `-3` |
| `%` | `%` | con negativos cambia: Python `-7 % 3` da `2`, JS da `-1` |
| `**` | `**` | |
| (no hay) | `n++`, `n--` | suman o restan 1 |
| `abs(x)`, `round(x)` | `Math.abs(x)`, `Math.round(x)` | `round(2.5)` en Python da `2`; `Math.round(2.5)` en JS da `3` |

### Comparación

| Python | JS |
|---|---|
| `==` (compara valor) | `===` (valor en primitivos; **referencia** en objetos) |
| `!=` | `!==` |
| `is` | `===` aplicado a objetos |
| `< > <= >=` | igual |
| `1 < x < 5` | `1 < x && x < 5` (la forma encadenada no funciona) |

### Lógicos, vacíos y condicionales

```js
a && b         // Python: a and b   (devuelve uno de los dos, igual que Python)
a || b         // Python: a or b
!a             // Python: not a
a ?? b         // a, salvo que sea null/undefined; entonces b   (a if a is not None else b)
a?.b           // a.b, pero si a es null/undefined devuelve undefined en vez de romper
c ? x : y      // x if c else y
```

### Asignación

```js
x += 1;  x -= 1;  x *= 2;  x /= 2;  x **= 2     // igual que Python
x ||= v        // x = x || v
x &&= v        // x = x && v
x ??= v        // si x es null/undefined, x = v    (como d.setdefault("k", v))
```

### Pertenencia, texto y listas

| Python | JS |
|---|---|
| `x in lista` | `lista.includes(x)` |
| `x not in lista` | `!lista.includes(x)` |
| `k in dict` | `k in obj` o `map.has(k)` |
| `x in set` | `set.has(x)` |
| `len(xs)` | `xs.length` |
| `xs[-1]` | `xs.at(-1)` (con `xs[-1]` obtienes `undefined`) |
| `xs[1:3]` | `xs.slice(1, 3)` |
| `s * 3` | `s.repeat(3)` |
| `"a" + "b"` | `"a" + "b"` (igual) |

Bits: `& | ^ ~ << >>` son iguales; JS añade `>>>`.

## Verdadero y falso

```
Python falso:  0  0.0  ""  []  {}  set()  None  False
JS falso:      0  -0  ""  null  undefined  NaN  false  0n
```

En JS, `[]` y `{}` son **verdaderos**.

## Trampas de tipos (JS convierte solo; Python da error)

```js
"5" + 1                // "51"        Python: TypeError
"5" - 1                // 4
"5" * 2                // 10
+"5"                   // 5           (el + delante convierte a número)
1 < 5 < 3              // true        (1 < 5 es true, y true < 3 es true). Python: False
NaN === NaN            // false       → usa  Number.isNaN(x)
null == undefined      // true
null === undefined     // false
10 in [10, 20]         // false       `in` en arreglos mira los ÍNDICES; Python: True
0.1 + 0.2              // 0.30000000000000004   (igual en Python)
```

## Las 6 que más caen en entrevista

1. `==` frente a `===`: usa siempre `===`.
2. `typeof null` es `"object"`.
3. `[]` y `{}` son verdaderos.
4. `||` frente a `??`: `0 || 5` da `5`; `0 ?? 5` da `0`.
5. `"5" + 1` da `"51"` (JS mezcla texto y número).
6. `%` con negativos, y `//` que no existe (`Math.floor(a / b)`).

# 00 · JS para pythonistas

> JS y Python hacen lo mismo con otra sintaxis. Esta ficha tiene las diferencias que te hacen perder puntos.

Reto: `retos/00-js-basico.js`

## Traducción directa

| Python | JS |
|---|---|
| `print(x)` | `console.log(x)` |
| `x = 5` | `const x = 5` (no se reasigna) o `let x = 5` (sí). Nunca `var` |
| `None` | `null` (vacío a propósito) y `undefined` (nadie lo asignó) |
| `==` | `===` (compara sin convertir tipos). Usa siempre `===` |
| `dict` | objeto `{ a: 1 }` o `Map` |
| `list` | arreglo `[1, 2]` |
| `set` | `Set` |
| `f"hola {n}"` | `` `hola ${n}` `` |
| `lambda x: x * 2` | `(x) => x * 2` |
| `[x*2 for x in xs]` | `xs.map(x => x * 2)` |
| `[x for x in xs if x > 1]` | `xs.filter(x => x > 1)` |
| `sum(xs)` | `xs.reduce((acc, x) => acc + x, 0)` |
| `len(xs)` | `xs.length` |
| `for x in xs:` | `for (const x of xs) { }` (con `of`, no `in`) |
| `a, b = par` | `const [a, b] = par` |
| `nombre = d["nombre"]` | `const { nombre } = d` |
| `{**a, "k": 1}` | `{ ...a, k: 1 }` |
| `d.get("k", 0)` | `d.k ?? 0` |
| `x if c else y` | `c ? x : y` |
| `import json` | `import fs from "node:fs"` |

## Qué se rompe: las 7 trampas

```js
// 1. sort() ordena como TEXTO y además MODIFICA el arreglo
[10, 2, 1].sort()                 // [1, 10, 2]
[...xs].sort((a, b) => a - b)     // ✔ copia + orden numérico

// 2. || trata el 0 como "vacío"; ?? solo reacciona a null/undefined
0 || 5                            // 5
0 ?? 5                            // 0   ← el d.get("k", 0) de JS

// 3. un arreglo vacío es VERDADERO (en Python es falso)
[] ? "sí" : "no"                  // "sí"

// 4. los objetos se comparan por referencia (en Python, == compara contenido)
const a = {}, b = {}; a === b     // false

// 5. + mezcla texto y número
"5" + 1                           // "51"      "5" - 1 → 4

// 6. \w solo entiende ASCII (en Python 3 entiende Unicode)
"canción".match(/\w+/g)           // ["canci", "n"]
"canción".match(/[\p{L}\p{N}_]+/gu)  // ["canción"] ✔

// 7. const no congela: impide reasignar, no modificar
const a = []; a.push(1)           // funciona
```

Falsos en JS: `0`, `""`, `null`, `undefined`, `NaN`, `false`. Todo lo demás es verdadero (también `[]` y `{}`).

## Regla de oro: copiar, no modificar

React te lo exigirá mañana. Hoy ve acostumbrándote:

```js
const b = [...a, nuevo];        // arreglo nuevo con uno más
const o2 = { ...o, edad: 31 };  // objeto nuevo con un campo cambiado
const c = a.filter(x => x.id !== id);   // arreglo nuevo sin uno
```

## Pregunta de entrevista → respuesta de una frase

- **¿`let`, `const`, `var`?** `const` por defecto, `let` si vas a reasignar; `var` es viejo y se escapa del bloque.
- **¿`==` o `===`?** `==` convierte tipos antes de comparar; `===` no. Uso `===`.
- **¿`null` o `undefined`?** `null` es vacío a propósito; `undefined` es que nadie lo asignó.
- **¿Qué es un closure?** Una función que recuerda las variables del lugar donde nació (igual que en Python).
- **¿`map` o `forEach`?** `map` devuelve un arreglo nuevo; `forEach` solo recorre y no devuelve nada.
- **¿Qué hace `...`?** Esparce un arreglo u objeto: sirve para copiar y para juntar.

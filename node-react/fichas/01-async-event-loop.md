# 01 · Async y event loop

> Node es **un solo mesero**. No se queda esperando a que la cocina termine un plato: toma el pedido, atiende otra mesa y entrega cuando la cocina avisa. Si el mesero se pone a cocinar él mismo, todo el restaurante se detiene.

Reto: `retos/01-async.js` · Recetas: R5 a R8

## Python → JS

| Python | JS |
|---|---|
| `asyncio` (event loop) | event loop (ya viene encendido) |
| `async def` / `await` | `async function` / `await` |
| `asyncio.gather(a, b)` | `Promise.all([a, b])` |
| `gather(..., return_exceptions=True)` | `Promise.allSettled([a, b])` |
| `asyncio.wait_for(x, t)` | `Promise.race([x, timeout])` |
| `time.sleep(2)` (bloquea) | un `for` de 3 s de CPU (bloquea) |
| hilos + GIL | un solo hilo |

Diferencia clave: en Python tú decides usar `asyncio`. En Node **todo el I/O ya es asíncrono**.

## Cómo funciona

```
tu código (1 solo hilo)
   │  "lee este archivo / llama a esta API / espera 1 s"
   ▼
el sistema operativo hace la espera  →  avisa  →  fila de espera  →  tu función corre
                                                   (solo cuando el hilo está libre)
```

El hilo nunca espera. Por eso Node aguanta miles de conexiones abiertas. Pero si **tu** código ocupa el hilo, nadie más avanza.

## Promesas en un minuto

Una **Promesa** es un vale: «tu resultado llegará después». En Python se parece a un `Future`.

Tiene tres estados: **pendiente** → **cumplida** (con un valor) o **rechazada** (con un error).

```js
// Crear una: llamar a resolver(valor) = «ya terminó, aquí está el valor»
const p = new Promise((resolver, rechazar) => {
  setTimeout(() => resolver("listo"), 1000);   // dentro de 1 s se cumple
});

// Usarla, dos formas equivalentes:
p.then((valor) => console.log(valor));          // con .then
const valor = await p;                          // con await (más cómodo)

Promise.resolve(42);                            // una promesa que ya nace cumplida
```

`setTimeout(f, ms)` ejecuta `f` cuando pasan `ms` milisegundos. `process.nextTick(f)` (solo Node) ejecuta `f` lo antes posible, justo al terminar lo que está corriendo y antes que las promesas.

## El orden, paso a paso

```js
console.log("1");                                  // sale YA: 1
setTimeout(() => console.log("2"), 0);             // agenda el 2 en la fila de timers
Promise.resolve().then(() => console.log("3"));    // agenda el 3 en la fila de promesas
process.nextTick(() => console.log("4"));          // agenda el 4 en la fila de nextTick
console.log("5");                                  // sale YA: 5
```

Al terminar el código normal, el hilo vacía las filas en este orden: nextTick (4), promesas (3), timers (2). Salida: **1, 5, 4, 3, 2** (en CommonJS; en un módulo ES sale 1, 5, 3, 4, 2).

## Qué se rompe sin esto

1. **Un endpoint con 3 s de CPU:** durante esos 3 s nadie más recibe respuesta (un solo mesero).
2. **Olvidas `await`:** recibes `Promise { <pending> }`, no el valor.
3. **Un `async` falla sin `try/catch`:** sale "unhandled rejection" y el proceso puede caerse.
4. **`await` dentro de `forEach`:** no espera, porque `forEach` ignora las promesas. Usa `for...of`.
5. **`await` uno tras otro cuando podían ir juntos:** tres llamadas de 1 s tardan 3 s en vez de 1 s.

Arreglos para la CPU pesada: `worker_threads`, un proceso aparte, o una cola con workers (lo que ya diseñaste).

## El orden de la fila

1. Código normal (síncrono)
2. `process.nextTick`
3. Promesas (`.then` y lo que sigue a un `await`)
4. Timers y I/O (`setTimeout`)

Regla: **normal → nextTick → promesas → timers**.

```js
console.log("A");
setTimeout(() => console.log("B"), 0);   // espera su turno aunque sean 0 ms
console.log("C");
// A, C, B
```

Ojo: dentro de un módulo ES (`import`), a nivel superior, las promesas se atienden **antes** que `nextTick`. En CommonJS (`require`), `nextTick` va primero. Si te lo preguntan, di cuál estás asumiendo.

## Pregunta de entrevista → respuesta de una frase

- **¿Node es multihilo?** Tu código JS corre en un hilo; el I/O lo hace el sistema operativo, por eso aguanta muchas conexiones.
- **¿Cuándo Node es mala idea?** Cuando hay cálculo pesado de CPU en el hilo principal.
- **¿Callbacks, promesas, `async/await`?** Es lo mismo en tres estilos; `async/await` es la forma cómoda de usar promesas.
- **¿`Promise.all` o `allSettled`?** `all` falla en cuanto una falla; `allSettled` espera todas y te dice cuál falló.
- **¿Qué pasa con `await` dentro de `forEach`?** No espera; usa `for...of` o `Promise.all(xs.map(...))`.
- **¿Qué es el event loop?** El bucle que toma lo que está listo en la fila de espera y lo ejecuta cuando el hilo se libera.

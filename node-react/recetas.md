# Recetas · plantillas para memorizar

Cada receta es corta a propósito. Cómo usarlas: **léela, tápala y escríbela de memoria**. Al día siguiente, otra vez.

## Express

### R1 · Servidor mínimo

```js
import express from "express";

const app = express();
app.get("/", (req, res) => res.json({ ok: true }));
app.listen(3000, () => console.log("escuchando en 3000"));
```

### R2 · Esqueleto de una API

El orden es parte de la receta: **id → json → rutas → 404 → errores**.

```js
import express from "express";
import { randomUUID } from "node:crypto";

const falla = (req, code, message) => ({ error: { code, message, request_id: req.id } });

export function crearApp() {
  const app = express();

  app.use((req, res, next) => {            // 1. id de la petición
    req.id = randomUUID();
    res.setHeader("X-Request-Id", req.id);
    next();
  });
  app.use(express.json());                 // 2. leer el cuerpo JSON

  const r = express.Router();              // 3. rutas
  r.get("/", (req, res) => res.json(lista));
  r.get("/:id", (req, res) => { /* buscar con Number(req.params.id); 404 si no */ });
  r.post("/", (req, res) => { /* validar; res.status(201).location(...).json(nuevo) */ });
  r.delete("/:id", (req, res) => { /* 204 con res.status(204).end() */ });
  app.use("/tracks", r);

  app.use((req, res) =>                    // 4. 404: después de TODAS las rutas
    res.status(404).json(falla(req, "not_found", "ruta no encontrada")));

  app.use((err, req, res, next) => {       // 5. errores: 4 parámetros, al final
    if (err.type === "entity.parse.failed") {
      return res.status(400).json(falla(req, "bad_json", "JSON mal formado"));
    }
    console.error(err);                    // el detalle va al log, no al cliente
    res.status(500).json(falla(req, "internal_error", "error interno"));
  });
  return app;
}
```

### R3 · Middleware (tres lugares)

```js
const log = (req, res, next) => {
  const t0 = Date.now();
  res.on("finish", () => console.log(req.method, req.url, res.statusCode, `${Date.now() - t0}ms`));
  next();                                  // sin esto la petición se cuelga
};

app.use(log);                              // a todas las rutas
app.get("/privado", auth, handler);        // solo a esta ruta
router.use(auth);                          // a todo un router
```

### R4 · Validar entrada

```js
const esTexto = (v) => typeof v === "string" && v.trim() !== "";

const { title, artist } = req.body ?? {};  // ?? {} porque en Express 5 puede ser undefined
if (!esTexto(title) || !esTexto(artist)) {
  return res.status(400).json(falla(req, "validation_error", "title y artist son obligatorios"));
}
```

Con zod, la misma idea en una línea: `z.object({ title: z.string().min(1) }).safeParse(req.body)`.

## Async

### R5 · Esperar, en serie y en paralelo

```js
const esperar = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

// en serie: una tras otra (lento)
const a = await f1();
const b = await f2();

// en paralelo: todas a la vez (rápido)
const [x, y] = await Promise.all([f1(), f2()]);
const resultados = await Promise.all(tareas.map((t) => t()));
```

### R6 · Timeout

```js
async function conTimeout(promesa, ms) {
  let id;
  const limite = new Promise((_, rechazar) => {
    id = setTimeout(() => rechazar(new Error("timeout")), ms);
  });
  try {
    return await Promise.race([promesa, limite]);   // gana la primera que termine
  } finally {
    clearTimeout(id);                               // no dejes el temporizador vivo
  }
}
```

### R7 · Reintentos

```js
async function conReintentos(fn, n) {
  let ultimo;
  for (let i = 0; i < n; i++) {
    try {
      return await fn();
    } catch (e) {
      ultimo = e;
      // opcional: await esperar(2 ** i * 100);   ← backoff: 100, 200, 400 ms…
    }
  }
  throw ultimo;
}
```

### R8 · Errores con async

```js
try {
  const dato = await leer();
} catch (e) {
  // aquí llegan los errores de leer()
}

const res = await Promise.allSettled([a(), b()]);
// res = [{ status: "fulfilled", value }, { status: "rejected", reason }]
```

## Probar un API sin instalar nada

### R9 · `fetch` contra tu app

```js
import { once } from "node:events";

const servidor = crearApp().listen(0);            // 0 = puerto libre al azar
await once(servidor, "listening");
const base = `http://127.0.0.1:${servidor.address().port}`;

const res = await fetch(`${base}/tracks`, {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ title: "Intro", artist: "Ana" }),
});
console.log(res.status, await res.json());

servidor.close();
```

// SIMULACRO · RESPUESTA DE REFERENCIA (API de libros con Express)
//
// Es UNA forma de resolverlo, con comentarios sobre las decisiones importantes.
// Córrelo con:  node retos/simulacro-node-respuesta.js   → debe dar 19/19.
// Cópiale las partes que no sabías a TU archivo, pero escríbelas tú, no pegues.
//
// ── ENUNCIADO ───────────────────────────────────────────────────────────────────
// crearApp({ consultarRating }) devuelve una app de Express (SIN llamar a listen) con libros en memoria.
// Empieza vacía. Los ids son 1, 2, 3… y nunca se reutilizan.
// `consultarRating(id)` es una función async que te INYECTAN (consulta un servicio externo y
// devuelve un número). Si no la pasan, usa  async () => 4.
//
// RUTAS
//   GET    /books               → 200 { data: [...], page, limit, total }          (pública)
//   GET    /books/:id           → 200 { id, title, author, year } | 404             (pública)
//   POST   /books               → 201 + libro creado + cabecera Location: /books/<id>
//   DELETE /books/:id           → 204 sin cuerpo | 404
//   GET    /books/:id/rating    → 200 { id, rating }                                (pública)
//
// LIBRO: title y author = textos NO vacíos; year = número ENTERO entre 1000 y 2100 (un "1999" en texto no vale).
//
// LISTA  GET /books?author=<texto>&page=<n>&limit=<n>
//   · author (opcional): filtra por autor sin distinguir mayúsculas, coincidencia exacta.
//   · page por defecto 1; limit por defecto 10. Ambos enteros positivos; limit máximo 50.
//     Si no cumplen → 400 validation_error.
//   · total = cuántos libros hay DESPUÉS de filtrar y ANTES de paginar. Orden de inserción.
//   · Una página que ya no tiene libros devuelve 200 con data: [].
//
// AUTENTICACIÓN (solo POST y DELETE). Cabecera  Authorization: Bearer <token>
//   · token "admin-123"   → puede escribir
//   · token "lector-456"  → sabemos quién es, pero NO puede escribir → 403 forbidden
//   · sin cabecera, o token desconocido, o esquema que no sea Bearer → 401 unauthorized
//   · La autenticación se revisa ANTES que la validación del cuerpo y que el 404 del id.
//
// RATING  GET /books/:id/rating
//   · Si el libro no existe → 404 y NO se llama a consultarRating.
//   · Cada intento a consultarRating tiene un límite de 200 ms.
//   · Si un intento falla (rechaza o pasa de 200 ms) se reintenta UNA vez (2 intentos como máximo).
//   · Si el último intento falló por tiempo → 504 con code "timeout"; si falló por error → 502 con
//     code "upstream_error". Nunca devuelvas el mensaje del error real.
//
// ERRORES: todos usan el MISMO formato JSON (nunca HTML):
//   { "error": { "code": "...", "message": "...", "request_id": "<el mismo X-Request-Id>" } }
//   codes: validation_error · bad_json (400) · unauthorized (401) · forbidden (403) · not_found (404)
//          timeout (504) · upstream_error (502) · internal_error (500)
// Todas las respuestas llevan la cabecera X-Request-Id (distinta en cada petición).
// JSON mal formado → 400 bad_json.  Ruta inexistente → 404 not_found en JSON.

import express from "express";
import assert from "node:assert/strict";
import { once } from "node:events";
import { randomUUID } from "node:crypto";
import { chequear, resumen } from "./_util.js";

// ───────────── TU CÓDIGO ─────────────

// Quién es cada token. Un Map y no un objeto {}: con {} el token "constructor" o "toString"
// encontraría una función heredada y pasaría por válido.
const TOKENS = new Map([["admin-123", "admin"], ["lector-456", "lector"]]);

const esTexto = (v) => typeof v === "string" && v.trim() !== "";
const falla = (req, code, message) => ({ error: { code, message, request_id: req.id } });

// Los valores de req.query llegan como TEXTO (o undefined si faltan).
// Devuelve el número, el valor por defecto si no vino, o null si no es un entero positivo.
const entero = (v, defecto) => {
  if (v === undefined) return defecto;
  return typeof v === "string" && /^\d+$/.test(v) ? Number(v) : null;   // "1.5", "abc", "", "-1" → null
};

// Igual que el reto 01: carrera entre la promesa y un temporizador, y se limpia el temporizador.
function conTimeout(promesa, ms) {
  let id;
  const limite = new Promise((_, rechazar) => {
    id = setTimeout(() => rechazar(new Error("timeout")), ms);
  });
  return Promise.race([promesa, limite]).finally(() => clearTimeout(id));
}

export function crearApp({ consultarRating = async () => 4 } = {}) {
  const app = express();
  const libros = [];
  let siguiente = 1;

  // 1. id de la petición: ANTES de express.json(), para que hasta el error de JSON roto lleve el id
  app.use((req, res, next) => {
    req.id = randomUUID();                      // req, no res: es una propiedad de la petición
    res.setHeader("X-Request-Id", req.id);
    next();
  });
  app.use(express.json());

  // Middleware de autenticación: va SOLO en las rutas que escriben (POST y DELETE),
  // entre la ruta y el handler. Termina la petición (401/403) o llama a next().
  const escritura = (req, res, next) => {
    const h = req.headers.authorization ?? "";            // sin cabecera es undefined → "" para no romper
    const token = h.startsWith("Bearer ") ? h.slice(7) : null;
    const rol = TOKENS.get(token);
    if (!rol) return res.status(401).json(falla(req, "unauthorized", "falta autenticación"));   // no sé quién eres
    if (rol !== "admin") return res.status(403).json(falla(req, "forbidden", "sin permiso"));   // sé quién eres, no puedes
    next();
  };

  const buscar = (req) => libros.find((l) => l.id === Number(req.params.id));
  const noExiste = (req, res) => res.status(404).json(falla(req, "not_found", "libro no encontrado"));

  // LISTA: la ruta es solo "/books"; lo que va después del "?" se lee de req.query
  app.get("/books", (req, res) => {
    const page = entero(req.query.page, 1);
    const limit = entero(req.query.limit, 10);
    if (page === null || limit === null || page < 1 || limit < 1 || limit > 50) {
      return res.status(400).json(falla(req, "validation_error", "page y limit inválidos"));
    }
    const autor = req.query.author;
    const filtrados = typeof autor === "string"
      ? libros.filter((l) => l.author.toLowerCase() === autor.toLowerCase())
      : libros;
    const inicio = (page - 1) * limit;                    // la página 1 empieza en el índice 0
    res.json({
      data: filtrados.slice(inicio, inicio + limit),
      page,
      limit,
      total: filtrados.length,                            // total ANTES de recortar la página
    });
  });

  app.get("/books/:id", (req, res) => {
    const libro = buscar(req);
    if (!libro) return noExiste(req, res);
    res.json(libro);
  });

  app.post("/books", escritura, (req, res) => {          // primero la autenticación, luego el handler
    const { title, author, year } = req.body ?? {};
    if (!esTexto(title) || !esTexto(author) || !Number.isInteger(year) || year < 1000 || year > 2100) {
      return res.status(400).json(falla(req, "validation_error", "title, author y year son obligatorios"));
    }
    const libro = { id: siguiente++, title, author, year };
    libros.push(libro);
    res.status(201).location(`/books/${libro.id}`).json(libro);
  });

  app.delete("/books/:id", escritura, (req, res) => {
    const i = libros.findIndex((l) => l.id === Number(req.params.id));
    if (i === -1) return noExiste(req, res);
    libros.splice(i, 1);
    res.status(204).end();
  });

  // RATING: pública. Un bucle de 2 intentos; cada uno con límite de 200 ms.
  // Hay que recordar POR QUÉ falló el último intento para elegir 504 o 502.
  app.get("/books/:id/rating", async (req, res) => {      // async porque usa await
    const libro = buscar(req);
    if (!libro) return noExiste(req, res);                // si no existe, ni se llama al servicio
    let ultimo;
    for (let intento = 0; intento < 2; intento++) {
      try {
        const rating = await conTimeout(consultarRating(libro.id), 200);
        return res.json({ id: libro.id, rating });
      } catch (e) {
        ultimo = e;
      }
    }
    if (ultimo?.message === "timeout") {
      return res.status(504).json(falla(req, "timeout", "el servicio tardó demasiado"));
    }
    res.status(502).json(falla(req, "upstream_error", "el servicio de rating falló"));   // mensaje propio, no el del error
  });

  // 404 general: después de TODAS las rutas
  app.use((req, res) => res.status(404).json(falla(req, "not_found", "ruta no encontrada")));

  // Errores: 4 parámetros y al final de todo
  app.use((err, req, res, next) => {
    if (err.type === "entity.parse.failed") {                // así se llama el error de JSON mal formado
      return res.status(400).json(falla(req, "bad_json", "JSON mal formado"));
    }
    console.error(err);                                       // el detalle va al log, no al cliente
    res.status(500).json(falla(req, "internal_error", "error interno"));
  });

  return app;
}

// ───────────── PRUEBAS (no las edites) ─────────────

async function conApp(opciones, fn) {
  const servidor = crearApp(opciones).listen(0);
  await once(servidor, "listening");
  const base = `http://127.0.0.1:${servidor.address().port}`;
  try {
    await fn(base);
  } finally {
    servidor.close();
    servidor.closeAllConnections?.();
  }
}

const ADMIN = { authorization: "Bearer admin-123" };
const LECTOR = { authorization: "Bearer lector-456" };

const pedir = (base, metodo, ruta, { headers = {}, cuerpo } = {}) =>
  fetch(base + ruta, {
    method: metodo,
    headers: { ...(cuerpo !== undefined ? { "content-type": "application/json" } : {}), ...headers },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });

const libro = (n = 1, extra = {}) => ({ title: `Libro ${n}`, author: "Ana", year: 2000 + n, ...extra });

async function sembrar(base, libros) {
  for (const l of libros) {
    const res = await pedir(base, "POST", "/books", { headers: ADMIN, cuerpo: l });
    assert.equal(res.status, 201, "no se pudo crear un libro de prueba");
  }
}

async function verificarError(res, estado, codigo) {
  assert.equal(res.status, estado);
  assert.match(res.headers.get("content-type") ?? "", /json/, "el error debe ser JSON, no HTML");
  const cuerpo = await res.json();
  assert.equal(cuerpo.error?.code, codigo);
  assert.equal(typeof cuerpo.error?.message, "string");
  assert.ok(res.headers.get("x-request-id"), "falta la cabecera X-Request-Id");
  assert.equal(cuerpo.error?.request_id, res.headers.get("x-request-id"));
  return cuerpo;
}

await chequear("GET /books vacío (sin token) → 200 con page 1, limit 10, total 0", async () => {
  await conApp({}, async (base) => {
    const res = await pedir(base, "GET", "/books");
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { data: [], page: 1, limit: 10, total: 0 });
  });
});

await chequear("POST sin token, con token raro o con esquema que no es Bearer → 401 (aunque el cuerpo sea inválido)", async () => {
  await conApp({}, async (base) => {
    for (const headers of [{}, { authorization: "Bearer nadie" }, { authorization: "Bearer constructor" },
                           { authorization: "Basic admin-123" }, { authorization: "admin-123" }]) {
      await verificarError(await pedir(base, "POST", "/books", { headers, cuerpo: { title: "" } }), 401, "unauthorized");
    }
  });
});

await chequear("POST con token de lector → 403 forbidden", async () => {
  await conApp({}, async (base) => {
    await verificarError(await pedir(base, "POST", "/books", { headers: LECTOR, cuerpo: libro() }), 403, "forbidden");
  });
});

await chequear("POST válido (admin) → 201, objeto y Location; GET por id lo devuelve", async () => {
  await conApp({}, async (base) => {
    const res = await pedir(base, "POST", "/books", { headers: ADMIN, cuerpo: libro(1) });
    assert.equal(res.status, 201);
    assert.deepEqual(await res.json(), { id: 1, title: "Libro 1", author: "Ana", year: 2001 });
    assert.equal(res.headers.get("location"), "/books/1");
    const uno = await pedir(base, "GET", "/books/1");
    assert.equal(uno.status, 200);
    assert.deepEqual(await uno.json(), { id: 1, title: "Libro 1", author: "Ana", year: 2001 });
  });
});

await chequear("POST con datos inválidos → 400 validation_error (título vacío, autor no texto, year texto/decimal/fuera de rango)", async () => {
  await conApp({}, async (base) => {
    const malos = [libro(1, { title: "  " }), libro(1, { author: 5 }), libro(1, { year: "1999" }),
                   libro(1, { year: 1999.5 }), libro(1, { year: 999 }), libro(1, { year: 2101 }), { title: "x" }];
    for (const cuerpo of malos) {
      await verificarError(await pedir(base, "POST", "/books", { headers: ADMIN, cuerpo }), 400, "validation_error");
    }
  });
});

await chequear("POST sin cuerpo → 400 (no 500) y JSON mal formado → 400 bad_json", async () => {
  await conApp({}, async (base) => {
    await verificarError(await pedir(base, "POST", "/books", { headers: ADMIN }), 400, "validation_error");
    const roto = await fetch(base + "/books", {
      method: "POST",
      headers: { ...ADMIN, "content-type": "application/json" },
      body: "{oops",
    });
    await verificarError(roto, 400, "bad_json");
  });
});

await chequear("GET de un id que no existe o no numérico → 404 not_found", async () => {
  await conApp({}, async (base) => {
    await verificarError(await pedir(base, "GET", "/books/999"), 404, "not_found");
    await verificarError(await pedir(base, "GET", "/books/abc"), 404, "not_found");
  });
});

await chequear("filtro ?author= sin distinguir mayúsculas; total cuenta los filtrados", async () => {
  await conApp({}, async (base) => {
    await sembrar(base, [libro(1, { author: "Ana" }), libro(2, { author: "Beto" }), libro(3, { author: "ana" })]);
    const cuerpo = await (await pedir(base, "GET", "/books?author=ANA")).json();
    assert.deepEqual(cuerpo.data.map((l) => l.id), [1, 3]);
    assert.equal(cuerpo.total, 2);
    const nadie = await (await pedir(base, "GET", "/books?author=Zoe")).json();
    assert.deepEqual(nadie, { data: [], page: 1, limit: 10, total: 0 });
  });
});

await chequear("paginación: ?page=2&limit=2, última página parcial y página vacía", async () => {
  await conApp({}, async (base) => {
    await sembrar(base, [1, 2, 3, 4, 5].map((n) => libro(n)));
    const p2 = await (await pedir(base, "GET", "/books?page=2&limit=2")).json();
    assert.deepEqual(p2.data.map((l) => l.id), [3, 4]);
    assert.deepEqual([p2.page, p2.limit, p2.total], [2, 2, 5]);
    const p3 = await (await pedir(base, "GET", "/books?page=3&limit=2")).json();
    assert.deepEqual(p3.data.map((l) => l.id), [5]);
    const p4 = await pedir(base, "GET", "/books?page=4&limit=2");
    assert.equal(p4.status, 200);
    const cuerpo4 = await p4.json();
    assert.deepEqual(cuerpo4.data, []);
    assert.equal(cuerpo4.total, 5);
    const sinLimite = await (await pedir(base, "GET", "/books")).json();
    assert.equal(sinLimite.data.length, 5);
  });
});

await chequear("page/limit inválidos → 400 validation_error (0, negativo, texto, decimal, vacío, limit > 50)", async () => {
  await conApp({}, async (base) => {
    for (const q of ["page=0", "page=-1", "page=abc", "limit=0", "limit=51", "limit=1.5", "limit="]) {
      await verificarError(await pedir(base, "GET", `/books?${q}`), 400, "validation_error");
    }
    const ok = await pedir(base, "GET", "/books?limit=50");
    assert.equal(ok.status, 200);
  });
});

await chequear("DELETE: sin token 401, lector 403, inexistente 404, admin 204 sin cuerpo y luego 404", async () => {
  await conApp({}, async (base) => {
    await sembrar(base, [libro(1)]);
    await verificarError(await pedir(base, "DELETE", "/books/999"), 401, "unauthorized");
    await verificarError(await pedir(base, "DELETE", "/books/1", { headers: LECTOR }), 403, "forbidden");
    await verificarError(await pedir(base, "DELETE", "/books/999", { headers: ADMIN }), 404, "not_found");
    const borrar = await pedir(base, "DELETE", "/books/1", { headers: ADMIN });
    assert.equal(borrar.status, 204);
    assert.equal(await borrar.text(), "");
    await verificarError(await pedir(base, "GET", "/books/1"), 404, "not_found");
  });
});

await chequear("los ids no se reutilizan después de borrar", async () => {
  await conApp({}, async (base) => {
    await sembrar(base, [libro(1), libro(2)]);
    await pedir(base, "DELETE", "/books/2", { headers: ADMIN });
    const res = await pedir(base, "POST", "/books", { headers: ADMIN, cuerpo: libro(3) });
    assert.equal((await res.json()).id, 3);
  });
});

await chequear("X-Request-Id existe en cada respuesta (también en errores) y cambia en cada petición", async () => {
  await conApp({}, async (base) => {
    const ids = new Set();
    for (const [metodo, ruta] of [["GET", "/books"], ["GET", "/books"], ["POST", "/books"], ["GET", "/nada"]]) {
      const id = (await pedir(base, metodo, ruta)).headers.get("x-request-id");
      assert.ok(id, `falta X-Request-Id en ${metodo} ${ruta}`);
      ids.add(id);
    }
    assert.equal(ids.size, 4);
  });
});

await chequear("ruta inexistente → 404 en JSON", async () => {
  await conApp({}, async (base) => {
    await verificarError(await pedir(base, "GET", "/nada"), 404, "not_found");
  });
});

await chequear("rating: libro inexistente → 404 y NO llama al servicio", async () => {
  let llamadas = 0;
  await conApp({ consultarRating: async () => { llamadas++; return 5; } }, async (base) => {
    await verificarError(await pedir(base, "GET", "/books/7/rating"), 404, "not_found");
  });
  assert.equal(llamadas, 0);
});

await chequear("rating: éxito → 200 { id, rating } con una sola llamada (recibe el id como número)", async () => {
  const recibidos = [];
  await conApp({ consultarRating: async (id) => { recibidos.push(id); return 4.5; } }, async (base) => {
    await sembrar(base, [libro(1)]);
    const res = await pedir(base, "GET", "/books/1/rating");
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { id: 1, rating: 4.5 });
  });
  assert.deepEqual(recibidos, [1]);
});

await chequear("rating: si falla una vez se reintenta y responde 200 (2 llamadas)", async () => {
  let llamadas = 0;
  const flojo = async () => { llamadas++; if (llamadas === 1) throw new Error("secreto-rating"); return 3; };
  await conApp({ consultarRating: flojo }, async (base) => {
    await sembrar(base, [libro(1)]);
    const res = await pedir(base, "GET", "/books/1/rating");
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { id: 1, rating: 3 });
  });
  assert.equal(llamadas, 2);
});

await chequear("rating: si siempre falla → 502 upstream_error, exactamente 2 intentos y sin filtrar el error", async () => {
  let llamadas = 0;
  const roto = async () => { llamadas++; throw new Error("secreto-rating"); };
  await conApp({ consultarRating: roto }, async (base) => {
    await sembrar(base, [libro(1)]);
    const res = await pedir(base, "GET", "/books/1/rating");
    const texto = await res.clone().text();
    assert.ok(!texto.includes("secreto-rating"), "estás filtrando el mensaje del error real");
    await verificarError(res, 502, "upstream_error");
  });
  assert.equal(llamadas, 2);
});

await chequear("rating: si siempre tarda más de 200 ms → 504 timeout, 2 intentos y sin esperar al servicio", async () => {
  let llamadas = 0;
  const lento = () => { llamadas++; return new Promise((r) => setTimeout(() => r(5), 1500).unref()); };
  await conApp({ consultarRating: lento }, async (base) => {
    await sembrar(base, [libro(1)]);
    const t0 = Date.now();
    await verificarError(await pedir(base, "GET", "/books/1/rating"), 504, "timeout");
    assert.ok(Date.now() - t0 < 1200, "tardó demasiado: el límite de 200 ms no se está aplicando");
  });
  assert.equal(llamadas, 2);
});

resumen();

// Reto 02 · API de canciones con Express (60 min)
//
// Reglas del drill: a mano, sin IA, sin mirar otros archivos. Cronometra.
// Está resuelto cuando `node retos/02-express.js` termina con todos los chequeos en ✔.
// Ficha de apoyo: fichas/02-express.md
//
// ── ESPECIFICACIÓN ──────────────────────────────────────────────────────────────
// crearApp() devuelve una app de Express (SIN llamar a listen) con canciones en memoria.
// Empieza vacía; los ids son 1, 2, 3… y nunca se reutilizan.
//
//   GET    /tracks        → 200  [ { id, title, artist }, … ]
//   GET    /tracks/:id    → 200  { id, title, artist }   |  404 si no existe (o el id no es un número)
//   POST   /tracks        → body { title, artist }: dos textos NO vacíos
//                           201 + el objeto creado + cabecera Location: /tracks/<id>
//                           400 si falta algo, no es texto, o no viene cuerpo
//   DELETE /tracks/:id    → 204 sin cuerpo  |  404 si no existe
//   GET    /boom          → (ruta de prueba) lanza new Error("secreto-interno")
//   GET    /boom-async    → (ruta de prueba) igual, pero dentro de una función async
//   cualquier otra ruta   → 404
//
// Todas las respuestas llevan la cabecera X-Request-Id (un id distinto por petición).
// Todos los errores usan el MISMO formato JSON (nada de HTML):
//   { "error": { "code": "...", "message": "...", "request_id": "<el mismo X-Request-Id>" } }
//
//   400 datos inválidos   → code "validation_error"
//   400 JSON mal formado  → code "bad_json"        (¡el orden de los middleware importa!)
//   404                   → code "not_found"
//   500                   → code "internal_error"  (mensaje genérico: NO filtres el error real)

import express from "express";
import assert from "node:assert/strict";
import { once } from "node:events";
import { chequear, resumen } from "./_util.js";

// ───────────── TU CÓDIGO ─────────────

export function crearApp() {
  const app = express();
  // TODO
  return app;
}

// ───────────── PRUEBAS (no las edites) ─────────────

const servidor = crearApp().listen(0);
await once(servidor, "listening");
const base = `http://127.0.0.1:${servidor.address().port}`;

const enviarJSON = (metodo, ruta, cuerpo) =>
  fetch(base + ruta, {
    method: metodo,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(cuerpo),
  });

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

await chequear("GET /tracks vacío → 200 []", async () => {
  const res = await fetch(base + "/tracks");
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), []);
});

await chequear("POST /tracks válido → 201, objeto y cabecera Location", async () => {
  const res = await enviarJSON("POST", "/tracks", { title: "Intro", artist: "Ana" });
  assert.equal(res.status, 201);
  assert.deepEqual(await res.json(), { id: 1, title: "Intro", artist: "Ana" });
  assert.equal(res.headers.get("location"), "/tracks/1");
});

await chequear("GET /tracks/1 → 200 y aparece en la lista", async () => {
  const uno = await fetch(base + "/tracks/1");
  assert.equal(uno.status, 200);
  assert.deepEqual(await uno.json(), { id: 1, title: "Intro", artist: "Ana" });
  const lista = await (await fetch(base + "/tracks")).json();
  assert.equal(lista.length, 1);
});

await chequear("POST sin título → 400 validation_error", async () => {
  await verificarError(await enviarJSON("POST", "/tracks", { artist: "Ana" }), 400, "validation_error");
});

await chequear("POST con título vacío o que no es texto → 400", async () => {
  await verificarError(await enviarJSON("POST", "/tracks", { title: "  ", artist: "Ana" }), 400, "validation_error");
  await verificarError(await enviarJSON("POST", "/tracks", { title: 123, artist: "Ana" }), 400, "validation_error");
});

await chequear("POST sin cuerpo → 400 (no 500)", async () => {
  await verificarError(await fetch(base + "/tracks", { method: "POST" }), 400, "validation_error");
});

await chequear("POST con JSON mal formado → 400 bad_json", async () => {
  const res = await fetch(base + "/tracks", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{oops",
  });
  await verificarError(res, 400, "bad_json");
});

await chequear("GET de un id que no existe → 404 not_found", async () => {
  await verificarError(await fetch(base + "/tracks/999"), 404, "not_found");
});

await chequear("GET /tracks/abc (id no numérico) → 404", async () => {
  await verificarError(await fetch(base + "/tracks/abc"), 404, "not_found");
});

await chequear("ruta inexistente → 404 en JSON", async () => {
  await verificarError(await fetch(base + "/nada"), 404, "not_found");
});

await chequear("DELETE → 204 sin cuerpo; luego 404; los ids no se reutilizan", async () => {
  const borrar = await fetch(base + "/tracks/1", { method: "DELETE" });
  assert.equal(borrar.status, 204);
  assert.equal(await borrar.text(), "");
  await verificarError(await fetch(base + "/tracks/1"), 404, "not_found");
  await verificarError(await fetch(base + "/tracks/1", { method: "DELETE" }), 404, "not_found");
  const nueva = await enviarJSON("POST", "/tracks", { title: "Otra", artist: "Beto" });
  assert.equal((await nueva.json()).id, 2);
});

await chequear("X-Request-Id existe en cada respuesta y cambia en cada petición", async () => {
  const a = (await fetch(base + "/tracks")).headers.get("x-request-id");
  const b = (await fetch(base + "/tracks")).headers.get("x-request-id");
  assert.ok(a && b, "falta X-Request-Id");
  assert.notEqual(a, b);
});

await chequear("GET /boom → 500 internal_error y no filtra el mensaje real", async () => {
  const res = await fetch(base + "/boom");
  const texto = await res.text();
  assert.equal(res.status, 500);
  assert.ok(!texto.includes("secreto-interno"), "estás filtrando el mensaje del error");
  assert.ok(!texto.includes("node_modules"), "estás filtrando el stack");
  const cuerpo = JSON.parse(texto);
  assert.equal(cuerpo.error.code, "internal_error");
  assert.equal(cuerpo.error.request_id, res.headers.get("x-request-id"));
});

await chequear("GET /boom-async → 500 internal_error (error dentro de async)", async () => {
  await verificarError(await fetch(base + "/boom-async"), 500, "internal_error");
});

servidor.close();
servidor.closeAllConnections();
resumen();

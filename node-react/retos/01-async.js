// Reto 01 · async (45 min)
//
// Reglas del drill: a mano, sin IA, sin mirar otros archivos. Cronometra.
// Está resuelto cuando `node retos/01-async.js` termina con todos los chequeos en ✔.
// Ficha de apoyo: fichas/01-async-event-loop.md
//
// Antes de empezar, contesta en el chat (sin ejecutar nada): ¿en qué orden salen los números?
//
//   console.log("1");
//   setTimeout(() => console.log("2"), 0);
//   Promise.resolve().then(() => console.log("3"));
//   process.nextTick(() => console.log("4"));
//   console.log("5");

import assert from "node:assert/strict";
import { chequear, resumen } from "./_util.js";

// ───────────── TU CÓDIGO ─────────────

/** 1. Devuelve una promesa que se cumple (con undefined) después de `ms` milisegundos. */
export function esperar(ms) {
  throw new Error("TODO");
}

/** 2. `tareas` es un arreglo de funciones async (sin argumentos).
 *  Ejecútalas UNA tras otra y devuelve los resultados en el mismo orden. */
export async function enSerie(tareas) {
  throw new Error("TODO");
}

/** 3. Ejecuta todas A LA VEZ y devuelve los resultados en el orden de `tareas`
 *  (no en el orden en que terminan). */
export async function enParalelo(tareas) {
  throw new Error("TODO");
}

/** 4. Si `promesa` termina antes de `ms`, devuelve su valor.
 *  Si no, rechaza con new Error("timeout"). */
export async function conTimeout(promesa, ms) {
  throw new Error("TODO");
}

/** 5. Llama a `fn` hasta `n` veces EN TOTAL. Devuelve el primer éxito.
 *  Si las n veces fallan, lanza el ÚLTIMO error. */
export async function conReintentos(fn, n) {
  throw new Error("TODO");
}

// ───────────── PRUEBAS (no las edites) ─────────────

// Ayudante propio de las pruebas (no usa tu `esperar`).
const dormir = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

await chequear("esperar: devuelve una Promise que tarda al menos ms", async () => {
  const t0 = performance.now();
  const p = esperar(60);
  assert.ok(p instanceof Promise, "debe devolver una Promise");
  const valor = await p;
  assert.equal(valor, undefined);
  assert.ok(performance.now() - t0 >= 55, "terminó demasiado pronto");
});

await chequear("enSerie: una tarea empieza cuando termina la anterior", async () => {
  const log = [];
  const tarea = (nombre, ms) => async () => {
    log.push(`ini ${nombre}`);
    await dormir(ms);
    log.push(`fin ${nombre}`);
    return nombre;
  };
  const resultado = await enSerie([tarea("a", 30), tarea("b", 10)]);
  assert.deepEqual(resultado, ["a", "b"]);
  assert.deepEqual(log, ["ini a", "fin a", "ini b", "fin b"]);
});

await chequear("enParalelo: todas empiezan a la vez, resultados en orden de tareas", async () => {
  const log = [];
  const tarea = (nombre, ms) => async () => {
    log.push(`ini ${nombre}`);
    await dormir(ms);
    log.push(`fin ${nombre}`);
    return nombre;
  };
  const resultado = await enParalelo([tarea("a", 40), tarea("b", 10)]);
  assert.deepEqual(resultado, ["a", "b"]);
  assert.deepEqual(log, ["ini a", "ini b", "fin b", "fin a"]);
});

await chequear("enParalelo: 3 tareas de 60 ms tardan ~60 ms, no ~180 ms", async () => {
  const t0 = performance.now();
  await enParalelo([async () => dormir(60), async () => dormir(60), async () => dormir(60)]);
  const dt = performance.now() - t0;
  assert.ok(dt < 150, `tardó ${Math.round(dt)} ms: ¿las estás esperando una por una?`);
});

await chequear("conTimeout: si llega a tiempo, devuelve el valor", async () => {
  const valor = await conTimeout(dormir(10).then(() => "ok"), 100);
  assert.equal(valor, "ok");
});

await chequear("conTimeout: si no llega, rechaza con Error('timeout')", async () => {
  await assert.rejects(conTimeout(dormir(200).then(() => "tarde"), 30), { message: "timeout" });
});

await chequear("conReintentos: falla dos veces y la tercera funciona", async () => {
  let llamadas = 0;
  const inestable = async () => {
    llamadas++;
    if (llamadas < 3) throw new Error(`fallo ${llamadas}`);
    return "listo";
  };
  assert.equal(await conReintentos(inestable, 3), "listo");
  assert.equal(llamadas, 3);
});

await chequear("conReintentos: si funciona a la primera, no repite", async () => {
  let llamadas = 0;
  const bien = async () => {
    llamadas++;
    return 42;
  };
  assert.equal(await conReintentos(bien, 5), 42);
  assert.equal(llamadas, 1);
});

await chequear("conReintentos: si todas fallan, lanza el último error", async () => {
  let llamadas = 0;
  const malo = async () => {
    llamadas++;
    throw new Error(`fallo ${llamadas}`);
  };
  await assert.rejects(conReintentos(malo, 2), { message: "fallo 2" });
  assert.equal(llamadas, 2);
});

resumen();

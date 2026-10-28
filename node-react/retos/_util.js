// Mini-arnés de pruebas. No lo edites.
// Corre cada chequeo, imprime ✔ o ✘ (con el motivo) y un resumen al final.

let total = 0;
let bien = 0;

export async function chequear(nombre, fn) {
  total++;
  try {
    await fn();
    bien++;
    console.log(`  ✔ ${nombre}`);
  } catch (e) {
    const motivo = String(e?.message ?? e).replace(/\s+/g, " ").slice(0, 150);
    console.log(`  ✘ ${nombre}\n      → ${motivo}`);
  }
}

export function resumen() {
  console.log(`\n${bien}/${total} chequeos OK`);
  if (bien !== total) process.exitCode = 1;
}

// Reto 03 · Estado de React: contador y lista de tareas (60 min)
//
// Reglas del drill: a mano, sin IA. Cronometra.
// Está resuelto cuando `npm run reto3` (dentro de la carpeta react/) termina con todo en ✓.
// Ficha de apoyo: ../../fichas/04-react-estado-y-efectos.md
//
// ── ESPECIFICACIÓN ──────────────────────────────────────────────────────────────
// <Contador inicial={0} />                  (la prop `inicial` es opcional; por defecto 0)
//   · Muestra  <p>Cuenta: N</p>
//   · Botón «+1»          → suma 1
//   · Botón «+1 en 1 s»   → dentro de 1 segundo (setTimeout) suma 1 al valor MÁS RECIENTE
//   · Botón «Reiniciar»   → vuelve al valor de `inicial`
//
// <ListaTareas inicial={[]} />              (`inicial`: arreglo opcional de { id, texto, hecha }; NO lo modifiques)
//   · Un <form> con un <input> de etiqueta «Nueva tarea» (controlado) y un botón «Agregar»
//     de tipo submit. Enter y el botón hacen lo mismo. Al enviar, la página NO se recarga.
//   · Agregar recorta los espacios; si queda vacío, no agrega nada. Tras agregar, el input queda vacío.
//   · Muestra  <p>Pendientes: N</p>  = cuántas tareas NO están hechas. Se calcula, no es otro useState.
//   · Cada tarea es un <li> con:
//       - un checkbox cuya etiqueta es el texto de la tarea (marca hecha / no hecha)
//       - un <input aria-label="Nota de <texto>"> SIN controlar (no lo conectes a ningún estado)
//       - un botón con aria-label="Borrar <texto>" que quita ESA tarea
//   · Dos tareas pueden tener el mismo texto. Cada tarea necesita un id estable (no el índice).
//
// Pista de estructura: export function Contador(...) { ... }   export function ListaTareas({ inicial = [] }) { ... }

// ───────────── TU CÓDIGO ─────────────

export function Contador({ inicial = 0 }) {
  return null;
}

export function ListaTareas({ inicial = [] }) {
  return null;
}

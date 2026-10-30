// Reto 05 · Estilos en React: clases condicionales y `style` en línea (20 min)
//
// Reglas del drill: a mano, sin IA, SIN abrir recetas.md ni la ficha. Cronometra.
// Resuelto cuando `npm run reto5` (dentro de react/) termine con todo en ✓.
// Ficha de apoyo (para después): ../../fichas/05-react-estilos.md
//
// No hace falta escribir CSS: lo que se prueba es lo que React le pone a cada elemento.
// No uses ninguna librería (nada de clsx). React no debe mostrar NINGÚN aviso en la consola.
//
// ── <Boton variante="primario" activo deshabilitado onClick>texto</Boton> ───────────
//   · Renderiza un <button> con type="button" y como contenido sus `children`.
//   · variante: "primario" (por defecto) o "secundario".
//   · className = "btn btn--<variante>", y además "is-activo" SOLO si `activo` es verdadero.
//     Las clases van separadas por un solo espacio; no debe aparecer nunca «false», «undefined» ni «null».
//   · Si `deshabilitado` es verdadero, el botón queda disabled (y entonces no se llama a onClick).
//   · Un click llama a `onClick`.
//
// ── <Tarjeta ancho={240} color="red">contenido</Tarjeta> ────────────────────────────
//   · Un <div> con className="tarjeta" y los `children` dentro.
//   · Con estilo EN LÍNEA: width = `ancho` en píxeles (te pasan un número) y
//     backgroundColor = `color`.
//   · Si no pasan `ancho` (o `color`), ese estilo no se pone.
//
// ── <Cuadricula columnas={3} hueco={16}>hijos</Cuadricula> ──────────────────────────
//   · Un <div> con className="cuadricula" y los `children` dentro.
//   · Estilo en línea: display "grid", gridTemplateColumns "repeat(<columnas>, 1fr)" y gap = `hueco` en píxeles.
//   · Por defecto columnas = 3 y hueco = 16.

// ───────────── TU CÓDIGO ─────────────

export function Boton({ variante = "primario", activo = false, deshabilitado = false, onClick, children }) {
  return null;
}

export function Tarjeta({ ancho, color, children }) {
  return null;
}

export function Cuadricula({ columnas = 3, hueco = 16, children }) {
  return null;
}

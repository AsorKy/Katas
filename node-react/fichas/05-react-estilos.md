# 05 · React: estilos y maquetación con CSS

> En React el CSS sigue siendo CSS. Lo que cambia es **dónde lo escribes** y **cómo se lo pegas a cada elemento**.

Reto: `react/retos/05-estilos.jsx` · Recetas: R15 a R18

## Lo básico: `className`, no `class`

`class` es palabra reservada de JavaScript, así que en JSX se llama `className`. Otros nombres cambian por lo mismo:

| HTML | JSX |
|---|---|
| `class="btn"` | `className="btn"` |
| `for="correo"` | `htmlFor="correo"` |
| `style="color: red"` | `style={{ color: "red" }}` (un **objeto**, no un texto) |
| `onclick="..."` | `onClick={...}` |

## Las 5 formas de dar estilo

| Forma | Cómo se ve | Lo bueno | Lo malo |
|---|---|---|---|
| **CSS global** | `import "./app.css"` y `className="btn"` | simple; ideal para reset, tipografía, variables | las clases son globales: `.btn` de un archivo pisa a otro |
| **CSS Modules** | `import estilos from "./Tarjeta.module.css"` y `className={estilos.tarjeta}` | CSS normal (con `:hover`, media queries) y **local al componente** | un archivo más por componente |
| **Tailwind** | `className="flex items-center gap-4 p-4 hover:bg-gray-100 md:flex-row"` | rápido, sin inventar nombres, sin archivos CSS | JSX largo y hay que aprender el vocabulario |
| **CSS-in-JS** (styled-components) | `` const Boton = styled.button`padding: 8px;` `` | estilos con props dentro del componente | cuesta tiempo de ejecución; menos usado hoy |
| **`style` en línea** | `style={{ width: 240, backgroundColor: color }}` | valores calculados en ejecución | sin `:hover`, `:focus`, media queries ni pseudo-elementos |

Regla de bolsillo: **CSS Modules** (o Tailwind si el proyecto ya lo usa) para el diseño; CSS global solo para lo general; **`style` en línea solo para valores que salen de datos** (el ancho de una barra de progreso, un color que viene de la API).

### `style` en línea: tres reglas

```jsx
<div style={{ width: 240, backgroundColor: "red", opacity: 0.5 }} />
```
1. Es un **objeto** (dobles llaves: las de fuera son JSX, las de dentro son el objeto).
2. Los nombres van en **camelCase**: `backgroundColor`, no `background-color`.
3. Un **número** se convierte en píxeles (`240` → `240px`), salvo en propiedades sin unidad como `opacity`, `zIndex`, `flex` o `lineHeight`.

## Clases condicionales (sin librerías)

```jsx
const clases = ["btn", `btn--${variante}`, activo && "is-activo"].filter(Boolean).join(" ");
// → "btn btn--primario is-activo"   o   "btn btn--primario"
```

La trampa clásica: `` `btn ${activo && "is-activo"}` `` produce `"btn false"` o `"btn undefined"`. Por eso se usa un arreglo, `filter(Boolean)` y `join(" ")`. (Las librerías `clsx` y `classnames` hacen justo eso.)

## Flexbox: una dimensión (fila o columna)

```css
.centrado { display: flex; justify-content: center; align-items: center; }   /* centra en los dos ejes */
.fila     { display: flex; gap: 12px; align-items: center; }                  /* elementos en fila, con hueco */
```
- `justify-content` actúa en el **eje principal** (la fila); `align-items`, en el eje cruzado.
- `flex-direction: column` cambia la fila por columna; `flex-wrap: wrap` deja saltar de línea; `flex: 1` ocupa el espacio que sobra.

## Grid: dos dimensiones (rejilla)

```css
.rejilla  { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.tarjetas { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
```
La segunda es la rejilla de tarjetas **responsive sin media queries**: mete todas las columnas de al menos 220 px que quepan y reparte el resto.

¿Flex o grid? Flex para una barra o una fila de botones. Grid para una rejilla o un layout de página.

## Variables CSS y pseudo-clases

```css
:root { --acento: #4f46e5; --borde: #e5e7eb; }
.btn { background: var(--acento); }
.btn:hover { filter: brightness(1.1); }
.btn:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; }
```

`:hover`, `:focus-visible` y las media queries **no existen en `style` en línea**: ese objeto solo asigna propiedades a *ese* elemento, y los selectores viven en las hojas de estilo.

## Responsive (primero móvil)

```css
.pagina { display: grid; grid-template-columns: 1fr; gap: 16px; }                 /* móvil: una columna */
@media (min-width: 768px) { .pagina { grid-template-columns: 240px 1fr; } }       /* pantalla ancha: menú + contenido */
```
Hace falta `<meta name="viewport" content="width=device-width, initial-scale=1">` en el HTML. Prefiere `rem`, `%` y `clamp()` a píxeles fijos.

## Accesibilidad mínima (lo que se nota en una entrevista)

- **`<button>`** para acciones y **`<a>`** para navegar. Un `<div onClick>` no se alcanza con el teclado ni lo anuncia el lector de pantalla.
- **Foco visible**: no pongas `outline: none` sin dar otro indicador.
- **Contraste** del texto con el fondo de al menos 4.5 : 1.
- Cada `<input>` con su `<label>` (envolviéndolo o con `htmlFor`).
- `disabled` de verdad en los botones, no solo «gris».
- `type="button"` en botones que no envían un formulario (si no, dentro de un `<form>` lo envían).

## Qué se rompe sin esto

1. `class="btn"`: React avisa («Invalid DOM property»); usa `className`.
2. `style="color: red"` con texto: error; debe ser un objeto.
3. `style={{ "background-color": ... }}`: aviso; va en camelCase.
4. `` `btn ${activo && "x"}` ``: la clase se llama literalmente `false`.
5. Dos archivos con `.btn` en CSS global: uno pisa al otro y nadie sabe por qué.
6. `:hover` dentro de `style`: no funciona.
7. Un `<div>` como botón: sin teclado, sin foco, sin lector.
8. `style={{ width: "240" }}`: sin unidad no vale; usa el número `240` o `"240px"`.

## Pregunta de entrevista → respuesta de una frase

- **¿`className` o `class`?** `class` es palabra reservada de JavaScript; JSX usa `className`.
- **¿Por qué CSS Modules evita choques de nombres?** El build renombra cada clase con un sufijo único por archivo (`Tarjeta_tarjeta__x7f2a`), así que `.tarjeta` de un archivo no pisa a otro.
- **¿Por qué no puedo usar `:hover` en `style` en línea?** Porque `style` solo asigna propiedades a ese elemento; los selectores, las pseudo-clases y las media queries solo existen en hojas CSS.
- **¿Cuándo uso `style` en línea?** Para valores calculados en ejecución (ancho de una barra, un color que viene de datos), no para el diseño general.
- **¿Flexbox o Grid?** Flex para una dimensión (una fila o una columna); Grid para una rejilla de dos.
- **¿Cómo haces una rejilla de tarjetas responsive sin media queries?** `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))`.
- **¿Cómo centras un elemento?** `display: flex; justify-content: center; align-items: center` (o `display: grid; place-items: center`).
- **¿Cómo aplicas una clase según una prop?** Un arreglo con `filter(Boolean).join(" ")`; nunca `&&` dentro de una plantilla de texto.
- **¿Ventaja y coste de Tailwind?** Rápido y consistente, sin salir del JSX y sin inventar nombres; a cambio, JSX largo y hay que conocer el vocabulario.

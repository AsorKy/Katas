# node-react · repaso exprés

Preparación para la entrevista de **React y Node.js** (viernes 12:00). Todo a mano, sin IA.

## Cómo se estudia

1. **Lee la ficha** (5 min). Trae analogías con Python y lo que se rompe sin el concepto.
2. **Haz el reto sin mirar las recetas.** Cronometra.
3. **Compara con `recetas.md`.** Fíjate en lo que cambió.
4. **Tapa la receta y escríbela de memoria.** Repite mañana.

## Contenido

| Archivo | Qué es |
|---|---|
| [`fichas/00-js-para-pythonistas.md`](fichas/00-js-para-pythonistas.md) | Traducción Python → JS y las 7 trampas del lenguaje |
| [`fichas/00b-tipos-y-operadores.md`](fichas/00b-tipos-y-operadores.md) | Tipos de datos y operadores de JS frente a Python, con las trampas de conversión |
| [`fichas/01-async-event-loop.md`](fichas/01-async-event-loop.md) | Event loop, promesas y por qué un cálculo largo bloquea todo |
| [`fichas/02-express.md`](fichas/02-express.md) | Express: la tubería de middleware, errores y códigos HTTP |
| [`fichas/03-http-cors-contrasenas.md`](fichas/03-http-cors-contrasenas.md) | Parámetros, códigos HTTP, idempotencia, CORS y contraseñas |
| [`fichas/04-react-estado-y-efectos.md`](fichas/04-react-estado-y-efectos.md) | React: estado como foto fija, copiar sin mutar, `key`, formularios, efectos y hooks propios |
| [`fichas/05-react-estilos.md`](fichas/05-react-estilos.md) | React: `className`, CSS global/Modules/Tailwind, `style` en línea, clases condicionales, Flexbox, Grid y accesibilidad mínima |
| [`recetas.md`](recetas.md) | Plantillas de código cortas para memorizar |
| `retos/00-js-basico.js` | Cinco funciones: Map, agrupar, ordenar, `??` |
| `retos/01-async.js` | `esperar`, serie, paralelo, timeout, reintentos |
| `retos/02-express.js` | API de canciones con validación, errores y `X-Request-Id` |
| `react/retos/03-estado.jsx` | Contador y lista de tareas: estado, `key`, formulario controlado (con pruebas) |
| `react/retos/04-componentes-tipicos.jsx` | Buscador con debounce y carreras, lista paginada y detalle: los componentes típicos de una prueba (con pruebas, ~75 min) |
| `react/retos/05-estilos.jsx` | `Boton`, `Tarjeta` y `Cuadricula`: clases condicionales, estilo en línea y Grid (con pruebas, ~20 min) |
| `retos/simulacro-node.js` | Simulacro de 60 min: API de libros con paginación, autenticación 401/403 y servicio externo con timeout y reintento |

## Cómo se corre

```bash
cd node-react
npm install                       # una sola vez: instala express
node retos/00-js-basico.js        # sale ✔ o ✘ por cada chequeo y un resumen
```

Un reto está resuelto cuando el resumen dice que todos los chequeos están OK.

## Cómo se corre React

```bash
cd node-react/react
npm install                       # una sola vez
npm run reto3                     # ✓ por cada prueba que pasa, × con el motivo en las que fallan
npm run reto4                     # buscador, lista paginada y detalle
npm run reto5                     # estilos
```

Escribes tu código en `react/retos/0N-….jsx`; el archivo `.test.jsx` de al lado no se toca.

## Calendario

| Cuándo | Qué |
|---|---|
| Miércoles | Fichas 00 a 02 y sus retos |
| Jueves | React (hooks, estilos, formularios), Node intermedio (JWT, base de datos, streams), integración y simulacro |
| Viernes mañana | Repaso de fichas y recetas de memoria |

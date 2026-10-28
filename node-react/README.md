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
| [`fichas/01-async-event-loop.md`](fichas/01-async-event-loop.md) | Event loop, promesas y por qué un cálculo largo bloquea todo |
| [`fichas/02-express.md`](fichas/02-express.md) | Express: la tubería de middleware, errores y códigos HTTP |
| [`recetas.md`](recetas.md) | Plantillas de código cortas para memorizar |
| `retos/00-js-basico.js` | Cinco funciones: Map, agrupar, ordenar, `??` |
| `retos/01-async.js` | `esperar`, serie, paralelo, timeout, reintentos |
| `retos/02-express.js` | API de canciones con validación, errores y `X-Request-Id` |

## Cómo se corre

```bash
cd node-react
npm install                       # una sola vez: instala express
node retos/00-js-basico.js        # sale ✔ o ✘ por cada chequeo y un resumen
```

Un reto está resuelto cuando el resumen dice que todos los chequeos están OK.

## Calendario

| Cuándo | Qué |
|---|---|
| Miércoles | Fichas 00 a 02 y sus retos |
| Jueves | React (hooks, estilos, formularios), Node intermedio (JWT, base de datos, streams), integración y simulacro |
| Viernes mañana | Repaso de fichas y recetas de memoria |

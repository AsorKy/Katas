# 02 · Express

> Express es el FastAPI de Node. Cada petición pasa por una **tubería de funciones** (middleware) y la última responde. Si una función ni responde ni llama a `next()`, la petición se queda colgada.

Reto: `retos/02-express.js` · Recetas: R1 a R4

## FastAPI → Express

| FastAPI | Express |
|---|---|
| `app = FastAPI()` | `const app = express()` |
| `@app.get("/x")` | `app.get("/x", (req, res) => { ... })` |
| `APIRouter` | `express.Router()` |
| cuerpo con Pydantic | `req.body` (tras `app.use(express.json())`); validas tú |
| `/tracks/{id}` | `/tracks/:id` → `req.params.id` (**siempre texto**) |
| `?q=rock` | `req.query.q` |
| `return {...}` | `res.json({...})` (respondes tú, explícito) |
| `HTTPException(404)` | `res.status(404).json({...})` |
| `Depends` / middleware | `app.use(fn)` |
| `@app.exception_handler` | middleware de error: `(err, req, res, next)` |
| `uvicorn` | `app.listen(3000)` |
| `TestClient` | `fetch` contra `app.listen(0)` |

## La tubería

```
petición → [id] → [json] → [log] → [rutas /tracks] → respuesta
                                         │ error
                                         ▼
                              [404 si nadie respondió] → [error handler]
```

Se ejecuta **en el orden en que lo declaras**. Por eso el error handler va al final.

## Qué se rompe sin esto

1. **Sin `express.json()`:** `req.body` es `undefined`. En Express 5 también lo es si el cliente no manda cuerpo, así que `req.body.title` revienta con un 500. Usa `req.body ?? {}`.
2. **Un middleware que ni responde ni llama `next()`:** el cliente espera para siempre.
3. **Responder dos veces:** `Cannot set headers after they are sent`.
4. **Error handler mal puesto:** va al final y con **4 parámetros**. Con 3, Express no lo reconoce como handler de errores.
5. **`req.params.id` es texto:** `"1" === 1` es `false` y obtienes un 404 falso. Convierte con `Number(req.params.id)`.
6. **Orden equivocado:** si `express.json()` va antes del middleware que pone el id, un JSON mal formado falla sin id de petición.
7. **Express 4 frente a 5:** en el 4, un error dentro de una función `async` no llegaba al error handler (había que usar `try/catch` y `next(err)`). El 5 sí lo captura.

## Códigos HTTP que usarás

| Código | Cuándo |
|---|---|
| 200 | OK |
| 201 | creado (con `Location`) |
| 204 | borrado, sin cuerpo |
| 400 | petición mal hecha o datos inválidos |
| 401 | no hay sesión |
| 403 | hay sesión pero no tienes permiso |
| 404 | no existe |
| 409 | conflicto (ya existe) |
| 422 | validación (el que usa FastAPI; Express suele usar 400) |
| 500 | falló algo nuestro (mensaje genérico, sin filtrar el error real) |

## Estructura que se espera de un mid

- `crearApp()` **sin** `listen`: así se puede probar con `fetch` o con `supertest`.
- Capas: rutas (HTTP) → servicio (reglas) → datos (base). Las rutas no hablan con la base directamente.
- Un solo formato de error para toda la API, con `request_id`.

## Pregunta de entrevista → respuesta de una frase

- **¿Qué es un middleware?** Una función `(req, res, next)` que corre antes de la ruta: puede cambiar la petición, responder, o pasar al siguiente con `next()`.
- **¿Cómo manejas errores?** Un middleware de 4 parámetros al final; las rutas lanzan el error o llaman `next(err)`.
- **¿`app.use` o `app.get`?** `use` aplica a cualquier método bajo ese prefijo; `get` solo a GET en esa ruta exacta.
- **¿Cómo validas la entrada?** Nunca confío en `req.body`: lo valido (a mano o con zod) y respondo 400.
- **¿Por qué separar `crearApp()` de `listen()`?** Para poder probar la app sin abrir un puerto fijo.
- **¿Cómo escalas un API de Node?** Varias réplicas detrás de un balanceador (o `cluster`); el estado va fuera del proceso.

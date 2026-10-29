# 03 · HTTP, CORS y contraseñas

> Las preguntas de entrevista de Node/Express que no son código. Cada respuesta cabe en una frase.

## Dónde llegan los datos de la petición

| Dónde | Ejemplo de URL | Cómo se lee |
|---|---|---|
| `req.params` | `/tracks/5` | `req.params.id` → `"5"` (siempre texto) |
| `req.query` | `/tracks?artist=Ana&page=2` | `req.query.artist` |
| `req.body` | `POST` con JSON | `req.body` (solo existe si pusiste `express.json()`) |

FastAPI: parámetro de ruta, parámetro de query y modelo del cuerpo.

## Códigos de estado

| Código | Significa | Ejemplo |
|---|---|---|
| 200 | bien, con cuerpo | `GET /tracks` |
| 201 | creado | `POST` (con cabecera `Location`) |
| 202 | aceptada, se procesa después | trabajo en una cola |
| 204 | bien, sin cuerpo | `DELETE` |
| 400 | petición mal hecha | JSON roto, campo faltante |
| 401 | no autenticado: «¿quién eres?» | falta el token o es inválido |
| 403 | autenticado, sin permiso: «sé quién eres, pero no puedes» | un usuario normal pide algo de admin |
| 404 | no existe | id desconocido |
| 409 | conflicto | email ya registrado |
| 429 | demasiadas peticiones | límite de uso |
| 500 / 503 | falló el servidor / no disponible | |

## Idempotencia

**Idempotente** = repetir la petición deja el servidor en el **mismo estado final**.
`GET`, `PUT` y `DELETE` sí. `POST` no: dos `POST` crean dos tracks.
El código de respuesta puede cambiar (`DELETE` da 204 y luego 404) y sigue siendo idempotente, porque cuenta el estado, no la respuesta.
Para proteger un `POST` contra reintentos: cabecera `Idempotency-Key`.

## CORS

- Lo aplica el **navegador**, no el servidor. Una página en `localhost:5173` no puede leer respuestas de `localhost:3000` (otro puerto = otro origen), salvo que el servidor lo permita con la cabecera `Access-Control-Allow-Origin`.
- curl y Postman no lo aplican. Por eso «en Postman funciona y en React no».
- En Express:
  ```js
  import cors from "cors";
  app.use(cors({ origin: "http://localhost:5173" }));   // antes de las rutas
  ```
- Si la petición lleva JSON o `Authorization`, el navegador primero manda un `OPTIONS` (preflight) preguntando si puede. `cors()` lo contesta.
- En desarrollo hay otra salida: el proxy de Vite, que hace que el navegador solo vea un origen.

## Contraseñas

- Nunca se guardan en texto. Tampoco se **cifran**: se **hashean** con un algoritmo lento y con sal (`bcrypt`, `argon2` o `scrypt`).
- Cifrar es reversible: si se filtra la llave, se leen todas. Un hash no se puede revertir.
- Login: hasheas lo que escribió el usuario y lo comparas con el guardado (`bcrypt.compare`).
- **Sal**: texto al azar distinto por usuario; así dos contraseñas iguales dan hashes distintos.
- **Lento a propósito**: cada intento de fuerza bruta cuesta tiempo.
- Usa la versión asíncrona (`await bcrypt.hash(...)`): el cálculo no bloquea el hilo (ficha 01).

## Pregunta de entrevista → respuesta de una frase

- **¿401 o 403?** 401: no sé quién eres. 403: sé quién eres y no tienes permiso.
- **¿Por qué CORS falla en el navegador y no en Postman?** Porque la regla la aplica el navegador.
- **¿Cifrar o hashear contraseñas?** Hashear con sal y con un algoritmo lento; el cifrado se puede revertir.
- **¿`params`, `query` o `body`?** Ruta, después del `?`, y cuerpo del `POST`.
- **¿Es idempotente `DELETE`?** Sí: el estado final es el mismo aunque lo repitas.

---
tags: [fullstack-project-music, leccion, hecha]
leccion: 4
estado: hecha
---

# Lección 4 · Autenticación (Argon2, JWT, register, login, `/me`)

> **Objetivo:** que los usuarios puedan registrarse, iniciar sesión y probar quién son en cada petición. Se guarda la contraseña con **Argon2**, se emite un **JWT firmado con HS256** y se protege `GET /me` con una dependencia encadenada (`bearer` → `current_user`).
> Resultado final: `tests/test_auth_api.py` con **14 passed** y toda la suite en verde.

> En el diálogo original esta lección se llamó «Lección 6» (la numeración del diálogo no coincide con la de estos archivos). La siguiente del diálogo, «Lección 7» (escrituras protegidas), está en [[lesson-5]].

---

## 0. Dónde encaja

- Es el **cuarto paso de construcción** del plan: entorno ([[lesson-1]]) → contrato ([[lesson-2]]) → modelos, base y semilla ([[lesson-3]]) → **autenticación** → canciones y artistas ([[lesson-5]]) → playlists ([[lesson-6]]) → Dockerfile ([[lesson-7]]).
- **Orden real en clase:** la mitad de lectura de [[lesson-5]] (los `GET` públicos del catálogo y el sobre de errores) se hizo **antes** de esta lección; después de autenticar se hizo su mitad de escrituras protegidas (`POST /artists`, `POST /songs`). Los números de archivo siguen el plan de 7 pasos, no el orden cronológico exacto.
- **Depende de** [[lesson-3]]: la tabla `users` (`id`, `email` único, `password_hash`, `created_at`) y la sesión `get_db`.
- **De ella dependen** [[lesson-5]] (`POST /artists` y `POST /songs` usan `current_user`), [[lesson-6]] (`owned_playlist` se apoya en `current_user`) y [[lesson-9]] (el `LoginForm` de React guarda el token y lo manda como `Authorization: Bearer`).
- Parte del README que cubre: las filas `POST /auth/register`, `POST /auth/login` y `GET /me` del contrato, las reglas transversales («`password_hash` nunca sale en una respuesta», «Las contraseñas se guardan con hash (Argon2), jamás en claro») y el ítem `- [x] Autenticación` del checklist.

---

## 1. Qué se hizo (resumen)

1. **Punto de partida:** 47 tests en verde, 1 omitido y 13 en rojo (los 13 son `test_auth_api.py`, que ya estaban escritos pero sin código detrás).
2. **Paso 1:** tres campos nuevos en `config.py` (`secret_key`, `algorithm`, `access_token_minutes`) y el archivo nuevo `app/security.py` con cuatro funciones: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`.
3. **Paso 2:** `app/repositories/users.py` con `get_by_email` y `create_user` (6 tests, `test_users_repo.py`).
4. **Paso 3:** `POST /auth/register` (201 / 409) y `POST /auth/login` (200 / 401) en `routers/auth.py`.
5. **Paso 4:** `app/depends.py` con `bearer` y `current_user`, y `GET /me` en `routers/users.py`.
6. **Cierre:** quitar de `tests/test_contract.py` la aserción de que `/me` responde 501, marcar `[x] Autenticación` en el README y hacer el commit.

Archivos tocados (seis, más el test del contrato):

| Archivo | Estado | Qué hace |
|---|---|---|
| `app/config.py` | modificado | Clave secreta, algoritmo y minutos de vida del token |
| `app/security.py` | **nuevo** | Hashear/verificar contraseñas; crear/decodificar el JWT |
| `app/repositories/users.py` | **nuevo** | `get_by_email` y `create_user` |
| `app/depends.py` | **nuevo** | `bearer` y `current_user` |
| `app/routers/auth.py` | modificado | `register` y `login` |
| `app/routers/users.py` | modificado | `GET /me` |
| `tests/test_contract.py` | modificado | Fuera la aserción `/me == 501` |

Dependencias que ya estaban instaladas desde [[lesson-1]]: `pyjwt` (2.15.1 en `uv.lock`) y `pwdlib[argon2]` (pwdlib 0.3.1, que usa `argon2-cffi` 25.1.0 por debajo).

---

## 2. Paso a paso

### 2.0 Punto de partida

Antes de dar indicaciones se comprobó el estado del repo en una copia (nunca sobre tu código):

```bash
cd backend
uv run pytest -q                      # 13 failed, 47 passed, 1 skipped
uv run pytest -q tests/test_auth_api.py   # 13 failed, 1 passed
```

El único test de auth que ya pasaba era `test_register_short_password_is_422`: la validación de Pydantic (`password` con `min_length=8`) se ejecuta **antes** de entrar en la función, así que el 422 sale aunque el endpoint sea un stub 501.

Archivos que todavía **no** existían: `app/security.py`, `app/deps.py` (acabó llamándose `depends.py`) y `app/repositories/users.py`. `config.py` solo tenía `database_url`.

Orden de trabajo acordado (de abajo hacia arriba):

| Paso | Qué haces | Se pone en verde |
|---|---|---|
| 1 | `config.py` y `security.py` (hash y JWT) | se prueba a mano |
| 2 | `repositories/users.py` | `test_users_repo.py` (6) |
| 3 | `POST /auth/register` y `/auth/login` | registro y login (8) |
| 4 | dependencia `current_user` y `GET /me` | `/me` (6) |

Limpieza heredada de la lección anterior (se pidió antes de empezar): quitar `song_ids` de `seed.py`, poner `-> dict | None` en `get_stats`, marcar `[x]` en *Contrato* y *Modelos* del README, crear un `.gitignore` (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.DS_Store`, `backend/data/*.db`, `node_modules/`) y hacer el commit.

---

### 2.1 Paso 1 · `config.py` y `security.py`

**`app/config.py`**: se añaden tres campos a `Settings`:

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/music.db"
    secret_key: str = "dev-only-secret-change-me-via-env-0123456789"
    algorithm: str = "HS256"
    access_token_minutes: int = 60
```

- El valor por defecto de `secret_key` se mantiene con **al menos 32 caracteres**: PyJWT avisa si la clave para HS256 es más corta.
- Es un valor **solo para desarrollo**. En producción se sobrescribe con la variable de entorno `SECRET_KEY` (pydantic-settings lee el entorno y gana al valor por defecto). Ver [[#4. Qué NO hacer|«Qué NO hacer»]].

**Esqueleto que se dio** (los `...` eran lo que había que rellenar):

```python
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

_hasher = PasswordHash.recommended()     # Argon2


def hash_password(password: str) -> str:
    return ...

def verify_password(password: str, password_hash: str) -> bool:
    return ...


def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": ..., "exp": exp}                    # sub: ¿qué tipo exige JWT?
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[...])
        return ...                                         # el id como int
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
```

En este punto dijiste que no podías seguir por tu cuenta y pediste la solución de cada función con su explicación. Se ejecutó primero en una copia (no se tocó tu repo) y salió **un aviso de ruff**: `UP017`, usar `datetime.UTC` en vez de `timezone.utc`. Es estético, pero se adoptó la forma moderna.

**Versión final (`app/security.py`)**, tal como está hoy en tu repo:

```python
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

_hasher = PasswordHash.recommended() # Argon2


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
```

> Detalle menor: en una versión intermedia tu `except` incluía también `jwt.ExpiredSignatureError`. Sobraba porque es subclase de `InvalidTokenError`; ya lo quitaste.

**Cómo se probó (a mano, sin pytest):**

```bash
cd backend
uvx ruff check app/security.py            # estilo
uv run python -c "import app.security"    # ¿importa? (caza typos de módulos)
uv run python -c "
from app.security import *
h = hash_password('clave-123'); print(h[:15], verify_password('clave-123', h), verify_password('otra', h))
print(decode_access_token(create_access_token(7)), decode_access_token('basura'))"
```

**Salida esperada:**

```
$argon2id$v=19$ True False
7 None
```

**Hechos que se comprobaron ejecutándolos** (y que luego se explicaron):

| Prueba | Resultado |
|---|---|
| Hashear dos veces `"x"` | Hashes **distintos** (salt aleatorio), longitud **97** |
| `verify_password("x", h1)` y `("x", h2)` | `True` con ambos |
| Cabecera del JWT | `{'alg': 'HS256', 'typ': 'JWT'}` |
| Payload del JWT | `{'sub': '7', 'exp': 1792770577}` (el `datetime` se convierte en número) |
| `sub` entero al crear y decodificar | `InvalidSubjectError - Subject must be a string` (falla al **decodificar**, no al crear) |
| `jwt.decode` sin `algorithms=[...]` | `DecodeError` |
| Token caducado | `decode_access_token` → `None` |
| Payload manipulado (`sub` 7 → 1 con la firma vieja) | `decode_access_token` → `None` |

---

### 2.1b Aclaraciones del Paso 1 (preguntas tuyas)

#### «¿El hash es lo mismo que la firma?» → No. Dos mecanismos, cuatro funciones, dos parejas

```
REGISTRO  (POST /auth/register)
 "clave-123" ──hash_password──▶ "$argon2id$..." ──▶ [BD: users.password_hash]


LOGIN  (POST /auth/login)
 "clave-123" (lo que escribe) ──┐
                                ├──verify_password──▶ ¿True?
 [BD: users.password_hash] ─────┘                        │ sí
                                                         ▼
                                      user.id ──create_access_token──▶ JWT ──▶ al cliente
                                                                       (lo guarda)

PETICIÓN PROTEGIDA  (GET /me)
 header "Authorization: Bearer <JWT>" ──decode_access_token──▶ user_id ──▶ db.get(User, id)
                                               │
                                               └─ firma mala / caducado ──▶ None ──▶ 401
```

- **Pareja de contraseñas:** `hash_password` (guardar) y `verify_password` (comprobar). Actúan en registro y login.
- **Pareja de tokens:** `create_access_token` (emitir) y `decode_access_token` (leer y validar). Actúan después del login.
- **El único punto de contacto es el login:** si `verify_password` da `True`, se llama a `create_access_token`. La contraseña **nunca** viaja dentro del token.

| | Hash de contraseña | Firma del JWT |
|---|---|---|
| Pregunta que responde | «¿esta contraseña es la correcta?» | «¿este token lo emití yo y nadie lo tocó?» |
| Funciones | `hash_password`, `verify_password` | `create_access_token`, `decode_access_token` |
| ¿Usa tu `secret_key`? | No (usa un salt aleatorio guardado dentro del propio hash) | Sí |
| Dónde vive el resultado | En tu base de datos | En el cliente, que lo envía en cada petición |
| Qué protege | Si roban la BD, no ven las contraseñas | Que nadie fabrique ni edite tokens |

Mnemotecnia: **hash = huella** (no reconstruyes la contraseña a partir de ella, solo compruebas si una contraseña produce la misma huella); **firma = sello de lacre** (cualquiera lee la carta, pero solo quien tiene el sello fabrica uno válido; cambias una letra y el sello ya no encaja).

#### «¿La firma se da en la línea del `return jwt.encode(...)`?» → Casi

Tu idea: la firma se crea en el `jwt.encode` de `create_access_token`. Correcto, con matices:

1. **La firma se crea en `encode` y se verifica en `decode`.** Tu primera intuición de contar también la línea del `decode` no estaba mal: `encode` la fabrica; `decode` la recalcula y la compara con la que trae el token.
2. **JWT no es el algoritmo.** JWT es el **formato** (*JSON Web Token*). El algoritmo que firma es **HS256** = HMAC con SHA-256 (se elige con `algorithm=settings.algorithm`).
3. **`exp` es la fecha de expiración, no de expedición**, y no va «junto al payload»: va **dentro** del payload, igual que `sub`. No hay una tercera cosa que se firme aparte.

Lo que hace `encode`:

1. Codifica header y payload (con `sub` y `exp` dentro) y los une con un punto: `header.payload`.
2. Calcula `HMAC-SHA256(secret_key, "header.payload")`. Eso es la firma.
3. Une todo: `header.payload.firma`.

Se comprobó reproduciendo la firma **a mano** con la librería estándar; sale idéntica a la de PyJWT:

```python
import jwt, hmac, hashlib, base64, json
key = "clave-secreta-de-prueba-con-32-bytes-o-mas"
token = jwt.encode({"sub": "7", "exp": 1893456000}, key, algorithm="HS256")
head, pay, sig = token.split(".")
firma_a_mano = base64.urlsafe_b64encode(
    hmac.new(key.encode(), f"{head}.{pay}".encode(), hashlib.sha256).digest()
).decode().rstrip("=")
print(sig == firma_a_mano)    # True
```

Por eso un token manipulado se rechaza: si alguien cambia el `sub`, el texto `header.payload` ya no es el mismo y la firma que trae no encaja; y como la clave es secreta, tampoco puede calcular una firma nueva que valga.

#### «¿Dónde se guardan el hash y la firma? ¿El hash es otra codificación?»

| Qué | Dónde | Quién lo guarda |
|---|---|---|
| **Hash de la contraseña** | Columna `users.password_hash` | El servidor |
| **Firma del token** | Dentro del propio JWT (tercera parte) | El **cliente** guarda el token entero y lo manda en cada petición |
| **`secret_key`** | `config.py` o variable de entorno `SECRET_KEY` | El servidor; nunca sale de ahí |

El servidor **no guarda ningún token ni ninguna firma**: cuando llega uno, recalcula la firma con la `secret_key` y la compara. Eso es lo que significa *stateless* y por qué no hace falta una tabla de sesiones.

Un hash es un string, pero **no es una codificación**:

- **Codificar** (base64) solo cambia la forma de escribir los mismos datos y se revierte sin clave. En la prueba, `clave-123` → `Y2xhdmUtMTIz` → vuelve a `clave-123`.
- **Hashear** destruye la información a propósito. No existe «deshashear».

Anatomía del hash Argon2 real que se generó:

```
$argon2id$v=19$m=65536,t=3,p=4$a454oQGYAdUYLxFROAybEw$kMjbq6Ma46HFRcLGZzkKu22FseOSwDWBWynaPIW0JP0
```

| Parte | Significado |
|---|---|
| `argon2id` | El algoritmo |
| `v=19` | Versión del algoritmo |
| `m=65536,t=3,p=4` | Costos: 64 MB de memoria, 3 pasadas, 4 hilos (lo que lo hace lento a propósito) |
| `a454oQGY…` | El **salt**, aleatorio y distinto en cada hash |
| `kMjbq6Ma…` | El resultado real del hash |

Todo lo que `verify_password` necesita está en ese mismo string (algoritmo, costos y salt), por eso basta **una sola columna** `password_hash` (~97 caracteres).

#### ¿Por qué `decode_access_token` devuelve `None` y no lanza el error?

`security.py` no sabe nada de HTTP. Decidir que un token malo significa **401** le toca a la dependencia `current_user` (Paso 4). Es el mismo reparto que en el catálogo: el repositorio devuelve `None` y el router decide el 404. El `except` cubre tres casos: `InvalidTokenError` (caducado, firma mala o basura), `KeyError` (el token no trae `sub`) y `ValueError` (el `sub` no es un número).

---

### 2.2 Paso 2 · `app/repositories/users.py`

**Tests** (los escribió el tutor): `tests/test_users_repo.py`, **6 tests**, sin HTTP:

| Test | Qué protege |
|---|---|
| `test_create_user_returns_user_with_generated_fields` | El repo guarda el hash **tal cual** (no hashea) y la base genera `id` y `created_at` |
| `test_get_by_email_finds_the_user` | Encuentra al usuario creado |
| `test_get_by_email_returns_none_when_missing` | Sin fila → `None` |
| `test_get_by_email_matches_the_right_user` | Con dos usuarios devuelve el correcto (caza el `where` olvidado) |
| `test_duplicate_email_is_rejected_by_the_database` | La columna `UNIQUE` lanza `IntegrityError`: última defensa |
| `test_create_user_is_committed` | Otra sesión (como otra petición HTTP) ve al usuario → hay `commit` |

**Cómo se validaron los tests** (método que se usó en todo el curso): se escribió una implementación de referencia en una copia, se comprobó que los tests pasan, y luego se **mutó** el código para ver que los tests detectan el fallo:

- Mutación «sin `where`» → falla `test_get_by_email_matches_the_right_user` ✔.
- Mutación «`flush` en vez de `commit`» → **los 5 tests pasaban** ✘: era un hueco del test. Se añadió `test_create_user_is_committed` (abre dos sesiones con `db_factory`) y la mutación pasó a fallar ✔.

**Esqueleto:**

```python
def get_by_email(db: Session, email: str) -> models.User | None:
    # una fila o None: ¿db.scalar o db.scalars?
    return db.scalar(select(models.User).where(...))


def create_user(db: Session, email: str, password_hash: str) -> models.User:
    user = models.User(email=..., password_hash=...)
    db.add(user)
    db....()          # guardar de verdad en la base
    db....(user)      # recargar para traer id y created_at
    return user
```

**Versión final** (la tuya, verificada):

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def get_by_email(db: Session, email: str) -> models.User | None:
    return db.scalar(select(models.User).where(models.User.email == email))


def create_user(db: Session, email: str, password_hash: str) -> models.User:
    user = models.User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

**Qué se practicó:**

- **`db.scalar` y no `db.scalars`**: quieres un único valor (el usuario o `None`).
- **`commit`**: `db.add` solo prepara el objeto en la sesión; no queda guardado hasta `commit`.
- **`refresh`**: `id` y `created_at` los genera la base al insertar; `refresh` los relee para que el objeto devuelto los tenga (sin él, `UserOut` puede fallar al serializar).
- **El repositorio recibe el hash ya hecho**: quien llama (el router) hashea. El repo solo guarda datos y no sabe de seguridad.
- **Email duplicado**: el repo no lo comprueba; lo hace el router (409). Pero la columna es `UNIQUE`, así que si dos peticiones llegaran a la vez la base rechazaría la segunda con `IntegrityError`.

**Comando y salida esperada:**

```bash
cd backend
uvx ruff check app tests
uv run pytest tests/test_users_repo.py -q     # 6 passed
```

#### Lo que falló aquí (diagnóstico del adjunto que pegaste)

1. **Los 24 avisos de ruff eran de estilo, no bugs:** `I001` (14, imports sin ordenar), `UP017` (3, `datetime.UTC`) y `B008` (7). `B008` («no llames a `Depends(...)` en el valor por defecto») es una **falsa alarma**: es la forma normal de FastAPI. `uvx ruff check --fix app tests` arregla 17 de los 24 (queda solo `B008`).
2. **El error real: `from pwlib import PasswordHash`** en `security.py` → debe ser `pwdlib` (falta la «d»). Ruff **no** lo detecta porque no comprueba que un módulo exista; Python sí: `ModuleNotFoundError: No module named 'pwlib'`. No se había notado porque `test_users_repo` no importa `security`; en el Paso 3 el router de auth lo importa y **toda la app habría dejado de arrancar**.
3. **Tres intentos de test fallaron por typos en el comando:** `uv pytests …` (no es un subcomando de `uv`), `uv run pytests …` (el programa es `pytest`) y `tests/test_uders_repo.py` (es `test_users_repo.py`).

**La comprobación que cubre el hueco de ruff** (se repite en cada paso a partir de aquí):

```bash
uv run python -c "import app.security"      # y luego: import app.main
```

Tras corregir la `d`: `import ok`, `6 passed` y suite en **53 passed, 13 failed** (los 13 de auth, que es lo esperado hasta el Paso 4).

---

### 2.3 Paso 3 · `POST /auth/register` y `POST /auth/login`

Aquí se usan juntas las tres piezas: `security.py`, el repositorio de usuarios y `Depends(get_db)`.

**Esqueleto:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import users as users_repo
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=UserOut)
def register_user(body: UserCreate, db: Session = Depends(get_db)):
    if users_repo.get_by_email(db, body.email) is not ...:
        raise HTTPException(status_code=..., detail=f"Email {body.email} is already registered")
    return users_repo.create_user(db, body.email, ...(body.password))


@router.post("/login", response_model=Token)
def login_user(body: UserCreate, db: Session = Depends(get_db)):
    user = users_repo.get_by_email(db, body.email)
    if user is None or not ...(body.password, user.password_hash):
        raise HTTPException(status_code=..., detail="Invalid email or password")
    return Token(access_token=...(user.id))
```

**Tu primera versión** (verde parcial: 55 passed, 11 failed) tenía **tres problemas**:

```python
# register
raise HTTPException(status_code=400, detail=f"Email {body.email} already registered")      # ✗ 400
return users_repo.create_user(db=db, email=body.email, password_hash=hash_password(body.email))  # ✗ hasheaba el email

# login
raise HTTPException(status_code=400, detail="Invalid email or password")                    # ✗ 400
```

| # | Problema | Efecto | Arreglo |
|---|---|---|---|
| 1 | `hash_password(body.email)` | **Bug de seguridad**: el hash guardado corresponde al correo, no a la contraseña. El login con la clave real falla (400) y, peor, quien conozca el correo de un usuario podría entrar usándolo como contraseña. Los tests lo detectaron | `hash_password(body.password)` |
| 2 | 400 al duplicar correo | Rompe el contrato (409) | `status_code=409` |
| 3 | 400 al fallar el login | Rompe el contrato (401) | `status_code=401` |

Bonus del 400: el mapa `CODES` de `main.py` (`{401: "unauthorized", 404: "not_found", 409: "conflict", 422: "validation_error"}`) no tiene el 400, así que habría caído en el valor por defecto `internal_error` y la respuesta diría `{"error": {"code": "internal_error", ...}}`: **mentira**, porque no es un error del servidor. Con 409 y 401 salen `conflict` y `unauthorized`.

Se verificó en una copia aplicando los arreglos por separado:

| Arreglo aplicado | Resultado de los 8 tests |
|---|---|
| Solo `body.email` → `body.password` | 3 failed, 5 passed |
| + 409 en register + 401 en login | **8 passed** |

**Versión final (`app/routers/auth.py`)**, la que tienes hoy:

```python
@router.post("/register", status_code=201, response_model=UserOut)
def register_user(body: UserCreate, db: Session = Depends(get_db)):
    if users_repo.get_by_email(db=db, email=body.email) is not None:
        raise HTTPException(status_code=409, detail=f"Email {body.email} already registered")
    return users_repo.create_user(db=db, email=body.email, password_hash=hash_password(body.password))


@router.post("/login", response_model=Token)
def login_user(body: UserCreate, db: Session = Depends(get_db)):
    user = users_repo.get_by_email(db=db, email=body.email)
    if user is None or not verify_password(password=body.password, password_hash=user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.id))
```

**Qué piensa cada línea:**

1. **Register: orden de operaciones.** Primero compruebas si el correo existe (409) y después hasheas y guardas. Hashear es lo más lento (Argon2 lo es a propósito), así que no tiene sentido hacerlo si vas a rechazar la petición.
2. **Por qué no sale el hash en la respuesta.** `create_user` devuelve el `User` completo (con `password_hash`), pero el router declara `response_model=UserOut` (`id`, `email`, `created_at`) y FastAPI **filtra** todo lo que no esté en ese schema. Lo comprueba `test_register_returns_user_without_password`.
3. **Login: un solo error para dos casos.** Correo inexistente y contraseña equivocada deben dar **el mismo 401 con el mismo mensaje**. Si dijeras «ese correo no existe» en uno y «contraseña incorrecta» en otro, cualquiera podría descubrir qué correos están registrados (**enumeración de usuarios**). `test_login_unknown_email_gives_same_error_as_wrong_password` compara los dos cuerpos de respuesta.
4. **`user is None or not verify(...)`: el orden importa.** Si `user` es `None`, el `or` corta y nunca llega a `user.password_hash` (daría `AttributeError`). Es *cortocircuito*.
5. **`Token(access_token=…)`.** El campo `token_type` ya vale `"bearer"` por defecto en el schema; solo pasas el token.

**Comando y salida esperada** (los 8 tests de registro/login; los 6 de `/me` siguen en rojo hasta el Paso 4):

```bash
cd backend
uvx ruff check --select F,E9 app tests
uv run python -c "import app.main"
uv run pytest tests/test_auth_api.py -k "register or login or password_is_stored or token_carries" -q
# 8 passed
```

Suite completa en este punto: **60 passed, 6 failed, 1 skipped** (el tutor corrigió su propia cifra: antes dijo 5 en rojo para `/me`; son 6).

**Decisión pendiente (no resuelta):** `DELETE /auth/logout` sigue como stub 501 en `routers/auth.py`. No está en el contrato del README. Con JWT no hay estado en el servidor, así que el *logout lo hace el cliente borrando su token*; la recomendación fue borrar el endpoint. Es opcional, pero la explicación sirve de respuesta de entrevista.

---

### 2.3b Aclaraciones del Paso 3 (preguntas tuyas)

#### «¿Cómo se relaciona `get_db` con el parámetro `db`? ¿Por qué `db` tiene `add`, `get`…?»

`get_db` y `db` **no son lo mismo**:

- **`get_db`** es una función, el *proveedor*. Vive en `app/db.py`: crea una sesión, la entrega con `yield` y, al terminar la petición, la cierra. En tu repo:

  ```python
  engine = make_engine(settings.database_url)
  SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

  def get_db():
      with SessionLocal() as session:
          yield session
  ```

- **`db`** es solo el nombre de un parámetro del endpoint, el *receptor*. Contiene lo que `get_db` entregó con `yield`. El nombre es una convención; lo que los conecta es `Depends(get_db)`.

```python
def list_genres(db: Session = Depends(get_db)):
#               │     │              └─ «para llenar este parámetro, ejecuta get_db»
#               │     └─ tipo (solo para el editor: autocompletado)
#               └─ nombre del parámetro (podría llamarse «sesion»)
```

Flujo por petición:

```
petición ──▶ ve Depends(get_db) ──▶ ejecuta get_db() hasta el yield
                                          │ (crea una Session)
                                          ▼
                       pasa esa Session como argumento "db" ──▶ corre tu función
                                          │
                       cuando tu función termina ──▶ get_db continúa tras el yield ──▶ cierra la sesión
```

- El `: Session` es solo una **anotación de tipo**; FastAPI decide qué inyectar por el `Depends`, no por el tipo.
- Los métodos (`add`, `get`, `scalars`, `execute`, `commit`, `refresh`) vienen de la clase **`Session`** de SQLAlchemy. **La sesión no es la conexión:**

  ```
  Session            ← lo que recibes como "db". Métodos: add, get, execute, commit...
     │               Además recuerda qué objetos has cargado y qué cambió.
     ▼
  engine             ← administra las conexiones y sabe hablar el «dialecto» SQLite
     ▼
  data/music.db      ← el archivo real
  ```

- `SessionLocal = sessionmaker(bind=engine)` es la **fábrica**; `SessionLocal()` es la sesión. Hay **una sesión por petición**.
- Esa misma `db` se pasa como argumento normal a los repositorios (`users_repo.get_by_email(db, …)`); los repositorios no crean sesiones, las **reciben**. Eso es *inyección de dependencias*, y por eso en los tests se puede cambiar el proveedor con `dependency_overrides[get_db]` (ver [[#3.8 `dependency_overrides` y la fixture `client`|3.8]]).

#### «¿Cómo valida `verify_password` si `_hasher` viene de una librería?»

`_hasher` es un objeto de `pwdlib` que ya sabe hacer Argon2; no guarda ningún secreto (`PasswordHash.recommended()` solo lo configura con Argon2 y valores seguros). `_hasher.verify(password, password_hash)` hace esto:

```
guardado = "$argon2id$v=19$m=65536,t=3,p=4$<SALT>$<HASH>"

1. Lee del string guardado: algoritmo, costos (m,t,p) y el salt
2. Calcula Argon2(password_escrita, mismo salt, mismos costos)  → hash_nuevo
3. Compara hash_nuevo con el <HASH> guardado
4. True si coinciden, False si no
```

Funciona aunque `hash_password` dé un resultado distinto cada vez porque el salt original **viaja dentro del string guardado**. No descifra nada: **recalcula y compara**. Por debajo `pwdlib` usa `argon2-cffi`; regla de oro: usas librerías probadas, no inventas criptografía.

| | Contraseña | JWT |
|---|---|---|
| Qué necesita para validar | Solo el string guardado | La `secret_key` de tu servidor |
| Cómo valida | Recalcula Argon2 y compara | Recalcula HMAC y compara |

#### «Si Argon2 es público, ¿alguien con mi BD puede volver a ver las contraseñas?»

**No puede revertir el hash**; que el algoritmo sea estándar significa que todos saben *cómo* calcula, no que se pueda ejecutar al revés. La seguridad no depende de que el algoritmo sea secreto. Lo que **sí** puede hacer el atacante es **adivinar**: para cada candidata toma el salt del propio hash robado, calcula Argon2 y compara. Se simuló:

```python
import time
from pwdlib import PasswordHash
H = PasswordHash.recommended()
debil  = H.hash("123456")
fuerte = H.hash("k7#Qv9-lamparaVerde_58")
diccionario = ["password", "qwerty", "admin", "123456", "iloveyou", "clave-123"]
for nombre, robado in [("usuario 1", debil), ("usuario 2", fuerte)]:
    t0 = time.perf_counter(); intentos = 0; hallada = None
    for candidata in diccionario:
        intentos += 1
        if H.verify(candidata, robado):
            hallada = candidata; break
    dt = time.perf_counter() - t0
    print(nombre, hallada, intentos, f"{dt/intentos*1000:.0f} ms por intento")
```

Resultado: `usuario 1` → contraseña `'123456'` encontrada en **4 intentos** (~138 ms por intento); `usuario 2` → **no encontrada** (~134 ms por intento).

- Una contraseña **débil** sí cae (cualquier diccionario la tiene).
- Una **larga e impredecible** resiste en la práctica: cada intento cuesta 64 MB y más de 100 ms; probar millones se vuelve inviable.
- **El salt no es secreto:** va dentro del hash y el atacante lo tiene. Sirve para que dos usuarios con la misma clave tengan hashes distintos y para impedir tablas precalculadas; obliga a atacar a cada usuario por separado.
- Por eso `UserCreate` exige `min_length=8` y en producción se añaden reglas más estrictas.

#### «¿Dónde está el hash cuando `verify_password` lo valida? Solo lo veo en RAM»

En la prueba manual estaba en una variable, correcto: **la conexión con la base es exactamente el Paso 3**. `verify_password` es una función pura (dos strings → `bool`); no sabe que existe una base. Quien le da el hash guardado es el **router**, después de leerlo:

```
REGISTRO
  body.password ──hash_password──▶ "$argon2id$..." ──create_user──▶ [music.db: users.password_hash]
                                                                            (guardado en disco)
LOGIN
  body.email ──get_by_email──▶ [music.db] ──▶ user.password_hash ─┐
  body.password ──────────────────────────────────────────────────┴──verify_password──▶ True / False
```

#### «¿Cómo recupera la identidad si el salt es aleatorio?»

El hash **nunca se usa para encontrar al usuario**. Son dos pasos:

1. **Identificar** con el correo: `get_by_email` devuelve la fila.
2. **Autenticar** con la contraseña: `verify_password` comprueba si la clave escrita corresponde a *ese* hash.

El salt es aleatorio solo al crear el hash (una vez, en el registro); después queda dentro del string guardado y `verify` lo lee de ahí. Nadie busca usuarios por hash.

---

### 2.4 Paso 4 · `current_user` y `GET /me`

Es el concepto más nuevo de la lección: **dependencias que dependen de otras**.

```
GET /me
 └─ get_current_user(user = Depends(current_user))      ← el endpoint
        └─ current_user(creds = Depends(bearer),        ← la dependencia nueva
                        db    = Depends(get_db))
               ├─ bearer  → lee el header "Authorization: Bearer <token>"
               └─ get_db  → la sesión de siempre
```

FastAPI resuelve el árbol de abajo hacia arriba y **después** ejecuta tu función. Si dos dependencias piden `get_db` en la misma petición, les entrega **la misma sesión** (no abre dos). La ventaja: cualquier endpoint protegido solo añade `user = Depends(current_user)`; si el token falta o es malo, FastAPI corta con 401 antes de ejecutar tu función.

**Esqueleto de `app/depends.py`** (el tutor lo llamó `deps.py`; tú lo creaste como `depends.py`):

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if creds is None:
        raise HTTPException(status_code=..., detail="Not authenticated")
    user_id = decode_access_token(creds....)         # ¿qué atributo guarda el token en texto?
    user = db.get(models.User, ...) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=..., detail="Invalid or expired token")
    return user
```

**Versión final** (en tu repo, parte de `depends.py` correspondiente a esta lección):

```python
bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db)
) -> models.User:
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing credentials")
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid user or email")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
```

> Nota: el mensaje del segundo caso sigue siendo `"Invalid user or email"`. El tutor sugirió `"Invalid or expired token"` porque aquí el fallo es del token; ningún test comprueba ese texto, así que es solo cosmético y queda como mejora opcional. Más abajo en el archivo hoy hay también `owned_playlist` (se añadió en [[lesson-6]]).

**Las tres formas de fallar, todas 401:**

1. No hay header → `creds is None`.
2. El token es basura, está caducado o lo firmó otra clave → `decode_access_token` devuelve `None`.
3. El token es válido pero **el usuario ya no existe** → `db.get` devuelve `None`.

El tercer caso es importante: una firma válida solo prueba que **tú emitiste** el token; no prueba que ese usuario siga en la base hoy. Por eso se consulta.

**`app/routers/users.py`** (versión final):

```python
from fastapi import APIRouter, Depends

from app.schemas import UserOut
from app import models
from app.depends import current_user


router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserOut)
def get_current_user(user: models.User = Depends(current_user)):
    return user
```

El endpoint está casi vacío: todo el trabajo lo hizo `current_user`. `response_model=UserOut` vuelve a filtrar y no deja salir `password_hash`. (Al final del archivo quedan comentadas tres líneas de un `DELETE /delete` que ya no existe; ver pendientes.)

**Comandos y salida esperada:**

```bash
cd backend
uvx ruff check --select F,E9 app tests
uv run python -c "import app.main"
uv run pytest tests/test_auth_api.py -q      # 14 passed
uv run pytest -q                             # suite completa en verde
```

---

### 2.4b Aclaraciones del Paso 4 (preguntas tuyas)

#### «¿Qué papel tiene `Depends(bearer)`? Yo entendía que compartía sesión con `get_db`»

`bearer` **no tiene nada que ver con la base de datos**. Su único trabajo es **sacar el token del header**. `bearer = HTTPBearer(auto_error=False)` es un objeto *llamable*; `Depends(bearer)` dice: «antes de ejecutar `current_user`, llama a `bearer` con la petición actual y pásame lo que devuelva». Versión simplificada escrita a mano de lo que hace:

```python
def bearer(request: Request):
    header = request.headers.get("Authorization")      # "Bearer eyJhbGciOi..."
    if not header:
        return None
    scheme, _, token = header.partition(" ")           # "Bearer"  y  "eyJhbGciOi..."
    if scheme.lower() != "bearer" or not token:
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
```

Lo que recibes en `creds`: `creds.scheme` (`"Bearer"`) y `creds.credentials` (el token). Por eso a `decode_access_token` se le pasa `creds.credentials`, **no** `creds` entero. `HTTPBearer` además registra el esquema en la documentación: es lo que añade el botón **Authorize** en `/docs`.

**Corrección sobre «la misma sesión»:** no es que `bearer` y `get_db` compartan nada. Son **dos proveedores independientes**, cada uno llena un parámetro distinto:

```
petición HTTP ──▶ bearer(request) ──▶ creds   (el token que mandó el cliente)
                  get_db()        ──▶ db      (la sesión de la base)
                                          │
                       current_user(creds, db) usa los dos
```

«La misma sesión» se refiere solo a `get_db`: si dos dependencias de la misma petición lo piden (p. ej. `current_user` y el propio endpoint), FastAPI da la misma `Session`.

Para qué sirve cada uno dentro de `current_user`:

1. `creds` responde «¿quién dice ser?» → `decode_access_token(creds.credentials)` da el `user_id`.
2. `db` responde «¿existe ese usuario?» → `db.get(models.User, user_id)`.

#### `auto_error=False`

Solo cambia qué pasa si el header falta o está mal formado: `bearer` devuelve `None` en lugar de lanzar **su propio** error, para que el 401 lo lance tu `current_user` con **tu formato** (`{"error": {...}}`).

#### «¿Cuál es la diferencia entre `bearer` y el token que se genera?»

Tres cosas con nombres parecidos:

| | Qué es | Dónde aparece |
|---|---|---|
| **El token** (JWT) | La credencial en sí: el texto `eyJhbGci…` que fabricó `create_access_token` | Respuesta del login y lo que guarda el cliente |
| **La palabra `Bearer`** | Etiqueta del protocolo HTTP: «lo que sigue es un token de portador» | El header: `Authorization: Bearer eyJ...` |
| **`bearer`** (minúscula, en tu código) | El objeto de FastAPI que lee ese header y separa la etiqueta del token | `bearer = HTTPBearer(...)` en `depends.py` |

Analogía: el token es la **entrada de cine**, `Bearer` es lo que dice el sobre («adjunto entrada») y el objeto `bearer` es el **acomodador** que abre el sobre y te da la entrada. Lo que valida y expira es la entrada.

Recorrido completo:

```
1. login        → el servidor responde {"access_token": "eyJ...", "token_type": "bearer"}
                                              ▲ el token (JWT)          ▲ la etiqueta

2. el cliente arma el header:   Authorization: Bearer eyJ...
                                               ▲ etiqueta ▲ token

3. el servidor, en current_user:
      bearer(request) → creds.scheme      = "Bearer"     (la etiqueta)
                        creds.credentials = "eyJ..."     (el token)
      decode_access_token(creds.credentials)  → user_id
```

El campo `token_type: "bearer"` del schema `Token` está para decirle al cliente qué etiqueta poner delante del token. «Bearer» significa *portador*: quien porta el token es aceptado sin más pruebas, por eso se trata como una **contraseña temporal** y se envía solo por HTTPS. Otros esquemas: `Basic` (lo que sigue es `usuario:contraseña` en base64); si alguien manda `Authorization: Basic …`, `bearer` ve que la etiqueta no es `Bearer` y devuelve `None`.

#### «¿Es `bearer` lo mismo que un middleware?» → No, es una dependencia

```
petición ──▶ [middlewares]        ──▶ routing ──▶ [dependencias del endpoint]   ──▶ tu función
             (todas las rutas)         (elige        bearer, get_db, current_user     (recibe los
             CORS, logs, tiempos       el endpoint)                                    valores)
```

| | Middleware | Dependencia (`Depends`) |
|---|---|---|
| Cuándo corre | En **todas** las peticiones | Solo en los endpoints que la declaran |
| Dónde en el recorrido | Antes de elegir el endpoint, envolviendo todo | Después de elegir el endpoint |
| Qué ve | La petición y la respuesta crudas | Los parámetros de ese endpoint |
| Qué entrega a tu función | Nada (puede modificar petición/respuesta) | Un valor que llega como parámetro (`db`, `creds`, `user`) |
| En `/docs` | No aparece | Sí, `bearer` crea el botón «Authorize» |
| Ejemplos | CORS, logs, medir tiempos, comprimir | `get_db`, `bearer`, `current_user` |

**Por qué la autenticación va en una dependencia:** la API mezcla rutas públicas (`/health`, `/auth/*`, `GET /songs`) y protegidas (`/me`, escrituras, playlists). Con una dependencia eliges endpoint por endpoint, y tu función recibe el `User` ya tipado. Con middleware correría en todas las rutas (tendrías que saltarte las públicas) y para pasar el usuario habría que usar `request.state`, sin tipo ni documentación. Se puede autenticar con middleware, pero en FastAPI lo idiomático es la dependencia: **buena respuesta de entrevista**.

En el proyecto todavía no había middleware; el primero fue `CORSMiddleware` ([[lesson-9]]). Los dos handlers de errores de `main.py` son un **tercer mecanismo**: no corren en cada petición, solo se activan cuando alguien lanza una excepción.

#### Errores de esta parte (router de `/me` y `depends.py`)

Lo que pegaste en el router:

```python
@router.get("", response_model=UserOut)
def get_current_user():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=UserOut)
def get_current_user(user: models.User = Depends(bearer)):
    return current_user(creds)
```

Se probó en cuatro variantes en una copia:

| Variante | Resultado de los 6 tests `/me` |
|---|---|
| V1: tu router pegado (stub duplicado + `Depends(bearer)` + `current_user(creds)`) | 6 failed (`assert 501 == 200`…) |
| V2: borro el stub pero dejo `Depends(bearer)` + `current_user(creds)` | 6 failed (`NameError: name 'creds' is not defined`) |
| V3: router correcto, pero `depends.py` aún con `return HTTPException` | 1 failed, 5 passed |
| V4: V3 + `raise` en lugar de `return` | **6 passed** (y suite: 65 passed + el test del contrato) |

Diagnóstico:

1. **El stub viejo seguía ahí.** Dos funciones `get_current_user` en la misma ruta `GET /me`: se registran las dos y **gana la primera que coincide** (el stub 501).
2. **`Depends(bearer)` debía ser `Depends(current_user)`.** `bearer` entrega credenciales, no un usuario; tu anotación decía `models.User` pero recibirías otra cosa.
3. **`return current_user(creds)` no funciona:** `creds` no existe ahí (`NameError`) y **una dependencia no se llama a mano**; la llama FastAPI, resuelve sus parámetros y te entrega el resultado en el parámetro `user`. El endpoint solo lo devuelve.
4. **Imports sobrantes** (`HTTPException`, `bearer`): ruff los marca con `F401`.
5. El archivo en disco además tenía un trozo a medias (`@router.get("", response_model=UserOut):` con dos puntos y un `def get_current_user` sin paréntesis) → `SyntaxError`.

Y en `depends.py`:

| Error | Efecto |
|---|---|
| `HTTPEception` (typo en el import) | `ImportError: cannot import name 'HTTPEception' from 'fastapi'. Did you mean: 'HTTPException'?` |
| `def curren_user` (falta la `t`) | El router importa `current_user` y no existe |
| `return HTTPException(...)` en vez de `raise` (caso «sin credenciales») | Ver la traza explicada justo abajo |
| Mensaje `"Invalid user or email"` | No describe el problema (el fallo es del token). Cosmético |

#### La traza larguísima: `ResponseValidationError` por `return HTTPException`

Casi todo el texto es el recorrido interno de FastAPI/Starlette; lo útil está al final:

```
response_content = HTTPException(status_code=401, detail='Missing credentials')
...
ResponseValidationError: 3 validation errors:
  ('response', 'id')          Field required   input: HTTPException(...)
  ('response', 'email')       Field required   input: HTTPException(...)
  ('response', 'created_at')  Field required   input: HTTPException(...)
```

Cómo leerlo: «lo que tu endpoint devolvió como respuesta fue un objeto `HTTPException`, no un usuario»; FastAPI lo validó contra `UserOut` y no encontró `id`, `email` ni `created_at`. `serialize_response` valida lo que **sale**, así que falla *al final*, cuando el endpoint ya devolvió algo.

Paso a paso del test `test_me_without_token_is_401` (`GET /me` sin header):

1. `bearer` devuelve `None`.
2. En `current_user` entra en `if creds is None:` y ejecuta `return HTTPException(...)`.
3. `return` **no lanza** nada: devuelve ese objeto como resultado, y FastAPI lo trata como «el usuario».
4. El endpoint hace `return user` (ese objeto).
5. FastAPI lo valida como `UserOut` y revienta.

Con `raise`, la ejecución se corta ahí y se activa el manejo de errores: el handler de `main.py` lo convierte en el 401 `{"error": {"code": "unauthorized", ...}}`. **Arreglo: una palabra** (`return` → `raise`).

---

### 2.5 Recapitulación tuya y correcciones

Tu recap contó cuatro archivos y se centró en `/me`. Correcciones del tutor:

1. **Son seis archivos, no cuatro** (tabla de la sección 1).
2. **`security.py` no sabe de la base de datos ni del esquema `Token`.** Solo recibe datos y devuelve datos: contraseña → hash, `user_id` → JWT, JWT → `user_id` o `None`. Quien comprueba que el usuario existe es el router de `auth.py`. `Token` es un schema de `schemas.py` (la forma de la respuesta del login). Y hashear no es codificar.
3. **`bearer` no se comunica con `security`.** Solo lee el header y separa el token. Quien llama a `decode_access_token` es `current_user`. `decode` valida firma y caducidad y no tiene que ver con el «login»: el login lo hace `auth.py` con `verify_password` y `create_access_token`.
4. **En `/me` el endpoint se ejecuta al final, no al principio:** FastAPI resuelve primero las dependencias y después corre tu función.

Los tres flujos completos:

```
POST /auth/register
  auth.py → get_by_email (¿ya existe? → 409) → hash_password → create_user → UserOut (201)

POST /auth/login
  auth.py → get_by_email → verify_password (mal → 401) → create_access_token → Token (200)

GET /me
  main (app, handlers) → ruta /me en users.py
  FastAPI resuelve, ANTES de ejecutar el endpoint:
      bearer       → lee el header, entrega el token
      get_db       → entrega la Session
      current_user → decode_access_token (security) → user_id
                     db.get(User, user_id) → User
  get_current_user(user) → return user → UserOut → respuesta (200)

  Si algo falla en current_user: raise HTTPException(401) → handler de main → {"error": {...}}
```

Matiz: `security` no «genera un output para `current_user` que se comunica con el router». `security` devuelve un `user_id` a `current_user`; `current_user` busca el `User` en la base y lo entrega a FastAPI; FastAPI lo inyecta como parámetro `user` del endpoint. **El router no llama a `depends`: se lo encuentra ya resuelto.**

---

### 2.6 Cierre de la lección

1. **Test del contrato:** con `/me` implementado, `test_stubs_answer_501` fallaba (`assert 401 == 501`). Se pidió quitar la línea `assert client.get("/me").status_code == 501`. En tu repo está **comentada** (`#assert client.get("/me")…`), y el test sigue existiendo para `/playlists` mientras duró [[lesson-6]].
   - Esto explicó un «tenemos verde» que no era total: habías corrido solo `test_auth_api.py`; la **suite completa** tenía 1 fallo (el del contrato). Moraleja: cierra siempre con `uv run pytest -q`, no con un archivo.
2. README: `- [x] Autenticación`.
3. Commit (los haces tú).

Cifras de la suite a lo largo de la lección:

| Momento | Resultado |
|---|---|
| Inicio | 47 passed, 13 failed, 1 skipped |
| Tras `security.py` + `users.py` (repo) | 53 passed, 13 failed, 1 skipped |
| Tu primer `auth.py` (con los 3 problemas) | 55 passed, 11 failed |
| `auth.py` corregido | 60 passed, 6 failed, 1 skipped |
| `/me` correcto, `return HTTPException` aún | 65 passed, 1 failed |
| Todo corregido (y línea del contrato quitada) | verde (66 passed + 1 skipped) |

Un error posterior relacionado con esta lección (ya en [[lesson-5]], al proteger `POST /artists`): `from app.security import current_user` → `ImportError: cannot import name 'current_user' from 'app.security'`. **`current_user` vive en `depends.py`, no en `security.py`.** Ruff no lo detecta; `import app.main` sí.

| Módulo | Qué tiene |
|---|---|
| `security.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_access_token` |
| `depends.py` | `bearer`, `current_user` (y más tarde `owned_playlist`) |

---

### 2.7 Probar a mano con `curl` 📝

> 📝 Esto **no se ejecutó en clase**; es el flujo del criterio «hecho» del README aplicado a esta lección. Las formas de respuesta salen del código y de los tests.

```bash
cd backend && uv run uvicorn app.main:app --reload      # otra terminal:

curl -s -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com","password":"supersecret1"}'
# 201 {"id":1,"email":"ana@example.com","created_at":"..."}   (sin password ni hash)

TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com","password":"supersecret1"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s localhost:8000/me -H "Authorization: Bearer $TOKEN"     # 200 con el usuario
curl -s localhost:8000/me                                       # 401 {"error":{"code":"unauthorized","message":"Missing credentials"}}
```

También en `http://localhost:8000/docs`: botón **Authorize** (lo crea `HTTPBearer`), pegas el token y pruebas `/me`.

---

## 3. Conceptos enseñados

### 3.1 Hash vs cifrado vs codificación

| | Reversible | Necesita clave | Ejemplo | Para qué |
|---|---|---|---|---|
| **Codificación** | Sí | No | base64 | Cambiar la forma de escribir datos |
| **Cifrado** | Sí | Sí | AES | Ocultar datos que luego quieres leer |
| **Hash** | **No** | No (el salt va dentro) | Argon2 | Comprobar sin poder recuperar |

Las contraseñas se **hashean**; nunca se guardan en claro ni «codificadas». La única operación posible con un hash es probar candidatas y comparar.

### 3.2 Argon2 y el salt

- Argon2 es un algoritmo **lento y que consume memoria a propósito** (64 MB, 3 pasadas, 4 hilos en `recommended()`; ~135 ms por intento en la prueba) para frenar la fuerza bruta.
- El **salt** es aleatorio por hash y viaja dentro del string. Efectos: dos usuarios con la misma clave tienen hashes distintos; no sirven tablas precalculadas; `verify` no puede comparar `hash_password(x) == guardado` (el salt cambia), por eso lee el salt del guardado y recalcula.
- `PasswordHash.recommended()` se crea **una vez a nivel de módulo** (`_hasher`), no dentro de cada función.
- Usa `pwdlib` (que envuelve `argon2-cffi`): no inventes tu propia criptografía.

### 3.3 JWT (JSON Web Token)

- Formato: `header.payload.firma`, tres partes separadas por puntos.
- **Va firmado, no cifrado:** header y payload están solo codificados (base64url) y cualquiera puede leerlos; la firma solo prueba que **nadie los modificó**. No metas datos sensibles.
- Claims usados: **`sub`** (quién; debe ser **string**, por eso `str(user_id)`; al decodificar `int(payload["sub"])`) y **`exp`** (expiración; PyJWT convierte el `datetime` a número y `decode` rechaza el token si ya pasó).
- Firma HS256 = **HMAC-SHA256**(`secret_key`, `header.payload`). Algoritmo **simétrico**: la misma clave firma y verifica.
- **`algorithms=[...]` es obligatorio al decodificar** (sin él, `DecodeError`). Es una protección: evita que un atacante declare en el header otro algoritmo (por ejemplo «ninguno») para saltarse la verificación. Tú dices cuál aceptas.
- `decode` hace tres comprobaciones a la vez: firma, `exp`, `sub` string.

### 3.4 Stateless (sin estado)

El servidor no guarda ningún token ni sesión: valida recalculando la firma. Consecuencias: no hay tabla de sesiones; **el logout lo hace el cliente borrando su token** (por eso `DELETE /auth/logout` no está en el contrato); el token es válido hasta que caduca (`access_token_minutes = 60`).

### 3.5 Esquema Bearer y `HTTPBearer(auto_error=False)`

Ver [[#2.4b Aclaraciones del Paso 4 (preguntas tuyas)|2.4b]]: el header `Authorization: Bearer <token>`; `creds.scheme` / `creds.credentials`; `auto_error=False` para que el 401 lo lance tu código con tu formato; el botón **Authorize** de `/docs`.

### 3.6 Códigos de estado y por qué cada uno

| Código | Dónde | Por qué |
|---|---|---|
| **201** | `POST /auth/register` | Recurso creado |
| **200** | `POST /auth/login`, `GET /me` | Éxito |
| **401** | login fallido; `/me` sin token/token malo/usuario inexistente | «No estás autenticado» |
| **409** | `register` con correo repetido | Conflicto con el estado actual |
| **422** | `password` < 8 caracteres; cuerpo mal formado | Validación de Pydantic |
| **501** | `logout` (stub) | No implementado |

Un **400** genérico no vale aquí: rompe el contrato y, en este proyecto, `CODES` lo traduciría a `internal_error`.

### 3.7 No filtrar si un correo existe (enumeración de usuarios)

Correo inexistente y contraseña mala → **mismo 401, mismo mensaje** (`"Invalid email or password"`). El test compara los dos cuerpos con `==`.

### 3.8 `dependency_overrides` y la fixture `client`

Los tests no usan `data/music.db`: `conftest.py` crea una base SQLite **en archivo temporal** (`db_factory`; archivo y no `:memory:` porque el `TestClient` ejecuta los endpoints en otro hilo y cada conexión a `:memory:` sería una base distinta y vacía) y sustituye el proveedor:

```python
@pytest.fixture
def client(db_factory):
    from fastapi.testclient import TestClient
    from app.db import get_db
    from app.main import app

    def override_get_db():
        with db_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Es posible porque los endpoints **reciben** la sesión con `Depends(get_db)` (inyección de dependencias) en lugar de crearla. Toda la cadena (`current_user` incluida) usa la base temporal sin tocar una línea de código de la app.

### 3.9 `Depends` encadenadas, caché por petición y orden de resolución

`current_user` depende de `bearer` y de `get_db`; el endpoint depende de `current_user`. FastAPI resuelve de abajo hacia arriba, y si dos dependencias piden la misma (`get_db`) en una petición, reutiliza **un único resultado** (la misma `Session`).

### 3.10 `dependencies=[Depends(current_user)]` vs `user = Depends(current_user)` (adelanto de [[lesson-5]])

- En el **decorador**: exige token válido pero **no te da el usuario**. Úsalo cuando solo necesitas el *permiso* (`POST /artists`, `POST /songs`).
- Como **parámetro**: te da el `User`. Úsalo cuando necesitas saber *quién* es (dueño de una playlist, `/me`).

### 3.11 `raise` vs `return` con excepciones

`raise` corta la función y activa los handlers; `return HTTPException(...)` devuelve el objeto como si fuera el valor normal (aquí, «el usuario») y falla más tarde, lejos del origen y con una traza confusa.

### 3.12 Capas: qué sabe cada archivo

| Capa | Sabe de | No sabe de |
|---|---|---|
| `security.py` | Hash y JWT (funciones puras) | HTTP, base de datos, `Token` |
| `repositories/users.py` | SQL, sesión | Hash, contraseñas, HTTP |
| `depends.py` | Cabeceras, 401, buscar el usuario | Cómo se crea un token |
| `routers/*.py` | HTTP, orden de operaciones, códigos | SQL |

### 3.13 Herramientas de diagnóstico (los tres comandos de siempre)

```bash
uvx ruff check --select F,E9 app tests     # nombres sin definir, imports sin usar, sintaxis
uv run python -c "import app.main"         # ¿arranca la app? (caza ImportError/ModuleNotFoundError)
uv run pytest tests/test_auth_api.py -k "register or login" -q    # -k selecciona tests por nombre
```

- `ruff` completo (sin `--select`) mezcla ruido estético (`I001`, `UP017`, `B008`). Para buscar bugs, `F` y `E9`.
- Ruff **no** ve módulos que no existen ni nombres mal importados de un módulo que sí existe; `import app.main` sí.

### 3.14 Los 14 tests de `test_auth_api.py`

Helpers: `register`, `login`, `auth_header` (registra, loguea y devuelve `{"Authorization": "Bearer …"}`) y `make_token(sub, delta, key)` (fabrica tokens a medida con `jwt.encode`).

| Grupo | Test | Qué protege |
|---|---|---|
| Registro | `test_register_returns_user_without_password` | 201, `id == 1`, sin `password` ni `password_hash` en el cuerpo |
| | `test_register_duplicate_email_is_409` | 409 con `error.code == "conflict"` |
| | `test_register_short_password_is_422` | `min_length=8` |
| | `test_password_is_stored_hashed` | La BD guarda un hash que empieza por `$argon2`, distinto de la clave |
| Login | `test_login_returns_bearer_token` | 200, `token_type == "bearer"`, token no vacío |
| | `test_login_wrong_password_is_401` | 401 `unauthorized` |
| | `test_login_unknown_email_gives_same_error_as_wrong_password` | Mismo cuerpo en ambos fallos |
| | `test_token_carries_user_id_and_expiry` | `sub == "1"` y `exp` en el futuro |
| `/me` | `test_me_with_valid_token` | 200 y el correo correcto |
| | `test_me_without_token_is_401` | 401 `unauthorized` |
| | `test_me_with_garbage_token_is_401` | `Bearer esto.no.es.un.jwt` |
| | `test_me_with_expired_token_is_401` | Token con `exp` hace 1 minuto |
| | `test_me_with_token_signed_by_someone_else_is_401` | Firmado con otra clave |
| | `test_me_with_token_of_nonexistent_user_is_401` | Firma válida pero usuario 999 inexistente |

Cada caso de fallo de `current_user` (sin header / token malo / usuario fantasma) tiene su propio test.

---

## 4. Qué NO hacer

| No hagas | Por qué | Qué hacer |
|---|---|---|
| Guardar contraseñas en claro o «codificadas» (base64) | Quien robe la base las lee | Hash con sal y lento (Argon2 vía `pwdlib`) |
| `hash_password(body.email)` en vez de `body.password` | El hash corresponde al correo: login roto y cuenta abierta a quien conozca el correo | `hash_password(body.password)`; hay test que lo caza |
| Dejar la `secret_key` por defecto en producción | Cualquiera con el código puede **firmar tokens válidos** | Inyectar `SECRET_KEY` por variable de entorno; nunca hornearla en una imagen ni subir `.env` (está en `.gitignore`) |
| Poner datos sensibles en el payload del JWT | Va codificado, no cifrado: se lee | Solo `sub` y `exp` |
| `jwt.decode` sin `algorithms=[...]` | Permitiría que el token elija su algoritmo | Lista explícita (`[settings.algorithm]`) |
| Mensajes distintos para «correo no existe» y «clave mala» | Enumeración de usuarios | Mismo 401 y mismo texto |
| Devolver `password_hash` (o el modelo ORM sin `response_model`) | Filtración | `response_model=UserOut` |
| `return HTTPException(...)` | No lanza nada | `raise HTTPException(...)` |
| Llamar a una dependencia a mano (`current_user(creds)`) | La resuelve FastAPI | `user: models.User = Depends(current_user)` |
| Usar 400 para errores de auth | Rompe el contrato y `CODES` lo etiqueta `internal_error` | 401 / 409 / 422 |
| Loguear tokens 📝 | Un Bearer es una contraseña temporal: quien lo lea entra como el usuario | No imprimirlos en logs; enviarlos solo por HTTPS |

> 📝 «Loguear tokens» es la consecuencia directa de la regla del diálogo («el token se debe tratar como una contraseña temporal y enviar solo por HTTPS»); no se discutió como punto aparte.

### Limitación conocida del proyecto 📝 (no se vio en clase)

`UserCreate.email` es un `str` simple: no se valida el formato de correo ni se normaliza (`Ana@example.com` y `ana@example.com` serían dos usuarios distintos, porque la comparación y el `UNIQUE` de SQLite son sensibles a mayúsculas por defecto). Mejoras posibles: `EmailStr` de Pydantic y pasar el correo a minúsculas antes de buscar y guardar. Si te lo preguntan en la entrevista, se menciona como límite consciente del ejercicio.

---

## 5. Cómo se relaciona con el ritme

**Con el README (el contrato):**

| Fila del contrato | Dónde se cumple | Test |
|---|---|---|
| `POST /auth/register` · 201 `UserOut` · 409 · 422 | `routers/auth.py::register_user` | `test_register_*`, `test_password_is_stored_hashed` |
| `POST /auth/login` · 200 `Token` · 401 | `routers/auth.py::login_user` | `test_login_*`, `test_token_carries_user_id_and_expiry` |
| `GET /me` · sí · 200 `UserOut` · 401 | `routers/users.py::get_current_user` | `test_me_*` |
| Regla: «`password_hash` nunca sale en una respuesta» | `response_model=UserOut` | `test_register_returns_user_without_password` |
| Regla: «contraseñas con hash (Argon2), jamás en claro» | `security.hash_password` | `test_password_is_stored_hashed` |
| Formato de error `{"error": {"code": …}}` con `unauthorized` / `conflict` | handlers + `CODES` en `main.py` | `error.code` en los tests |
| Checklist `- [x] Autenticación` | — | suite en verde |

**Con el resto del proyecto:**

- [[lesson-3]] puso `users.password_hash` y el `UNIQUE` del correo; aquí se usan.
- [[lesson-5]]: `POST /artists` y `POST /songs` se protegen con `dependencies=[Depends(current_user)]`.
- [[lesson-6]]: `owned_playlist` encadena una dependencia más sobre `current_user` y devuelve **404** (no 403) para playlists ajenas.
- [[lesson-9]]: el `LoginForm` hace `POST /auth/login`, guarda `access_token` y lo manda como `Authorization: Bearer …`; el CORS tiene que permitir ese header.
- [[lesson-7]]: la `secret_key` por defecto **no** debe llegar al contenedor; se pasa con `-e SECRET_KEY=…` / `--env-file`.

**Con la entrevista:** la parte «Python endpoints/DB/routers» casi seguro incluye auth. Lo más probable: registrar/loguear, proteger una ruta, explicar JWT y por qué no guardas la contraseña. Ver las preguntas de abajo.

---

## 6. Preguntas de entrevista

1. **¿Diferencia entre codificar, cifrar y hashear?** Codificar (base64) es reversible sin clave; cifrar es reversible con clave; hashear es de un solo sentido. Las contraseñas se hashean.
2. **¿Por qué Argon2 y por qué es lento a propósito?** Porque cada intento de adivinar cuesta tiempo y memoria (64 MB, ~135 ms aquí), lo que hace inviable la fuerza bruta masiva si roban la base.
3. **¿Qué es el salt y cómo verifica si es aleatorio?** Valor aleatorio por hash que evita hashes iguales y tablas precalculadas. Va dentro del string guardado; `verify` lo lee, recalcula con el mismo salt y compara.
4. **Si roban la tabla `users`, ¿qué pueden hacer?** No revertir los hashes; sí probar contraseñas candidatas contra cada uno. Las débiles caen (`123456` en 4 intentos), las largas resisten.
5. **¿Qué lleva un JWT y quién puede leerlo?** `header.payload.firma`. Cualquiera lee header y payload (solo codificados); la firma (HMAC-SHA256 con la `secret_key`) impide modificarlos.
6. **¿Por qué `sub` es string y qué pasa si no?** Lo exige el estándar; con un entero, el token se crea pero `decode` lanza `InvalidSubjectError`.
7. **¿Por qué `algorithms=[...]` en `decode`?** Para no aceptar el algoritmo que declare el token (ataque `none`/confusión de algoritmos).
8. **¿Qué significa stateless y cómo haces logout?** El servidor no guarda sesiones; el cliente borra el token. Por eso no hay `logout` en el contrato. 📝 Ampliación (no vista): para revocar antes de tiempo se usan expiraciones cortas + refresh tokens o una lista de tokens revocados, a costa de perder lo «sin estado».
9. **¿Por qué el mismo 401 si el correo no existe o la clave es mala?** Para no revelar qué correos están registrados (enumeración de usuarios).
10. **¿Por qué `current_user` vuelve a consultar la base si la firma ya es válida?** Una firma válida solo prueba que tú emitiste el token; el usuario pudo borrarse después. Hay test para ese caso (usuario 999).
11. **¿Dependencia o middleware para autenticar en FastAPI?** Dependencia: es por endpoint, entrega el `User` tipado al handler y sale en `/docs`; un middleware correría en todas las rutas y pasaría el usuario por `request.state` sin tipo.
12. **¿401, 403 o 404?** 401 = no autenticado (sin credenciales válidas). 📝 403 = autenticado pero sin permiso. En este proyecto una playlist ajena responde **404** para no confirmar que existe ([[lesson-6]]).
13. **¿Qué hace `auto_error=False`?** `bearer` devuelve `None` en vez de lanzar su propio error, para dar el 401 con el formato propio.
14. **¿Cómo pruebas endpoints protegidos sin tocar la base real?** `dependency_overrides[get_db]` con una base temporal; los tests se registran, hacen login y usan el token (`auth_header`).
15. **¿Qué pasa si dos peticiones registran el mismo correo a la vez?** El `UNIQUE` de la columna rechaza la segunda con `IntegrityError`; la comprobación previa del router solo da un error más amable en el caso normal.

---

## 7. Checklist / estado

- [x] `config.py`: `secret_key`, `algorithm`, `access_token_minutes`
- [x] `security.py`: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- [x] `repositories/users.py` + `test_users_repo.py` (6 passed)
- [x] `POST /auth/register` (201 / 409 / 422) y `POST /auth/login` (200 / 401)
- [x] `depends.py`: `bearer` y `current_user`
- [x] `GET /me` (200 / 401)
- [x] `tests/test_auth_api.py`: 14 passed
- [x] Aserción `/me == 501` quitada de `test_contract.py` (comentada)
- [x] README: `[x] Autenticación`
- [ ] (Opcional) Borrar el stub `DELETE /auth/logout` de `routers/auth.py`
- [ ] (Opcional) Borrar las 3 líneas comentadas del `DELETE /delete` al final de `routers/users.py`
- [ ] (Opcional) Cambiar `"Invalid user or email"` por `"Invalid or expired token"` en `current_user`
- [ ] (Opcional 📝) Validar el formato del correo (`EmailStr`) y normalizarlo a minúsculas
- [ ] Antes de producción: inyectar `SECRET_KEY` por entorno ([[lesson-7]])

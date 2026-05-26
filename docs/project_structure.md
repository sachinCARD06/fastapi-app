# Project Structure — Deep Level

Complete reference for every file in the project: what it does, what it exports, and how it connects to the rest of the codebase.

---

## Directory Tree

```
fastapi-app/
│
├── app/                            ← All application source code
│   ├── __init__.py
│   ├── main.py                     ← App factory (entry point)
│   │
│   ├── core/                       ← Shared infrastructure (config, DB, auth)
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── deps.py
│   │
│   ├── models/                     ← SQLAlchemy ORM models (DB tables)
│   │   ├── __init__.py             ← Imports all models for Alembic
│   │   └── user.py
│   │
│   ├── schemas/                    ← Pydantic v2 request/response shapes
│   │   ├── token.py
│   │   └── user.py
│   │
│   ├── repositories/               ← Raw database queries (no business logic)
│   │   ├── base.py                 ← Generic CRUD base class
│   │   └── user_repository.py
│   │
│   ├── services/                   ← Business logic (calls repositories)
│   │   └── user_service.py
│   │
│   ├── api/                        ← HTTP layer
│   │   ├── api_router.py           ← Root router (mounts v1)
│   │   └── v1/
│   │       ├── router.py           ← v1 router (mounts all endpoints)
│   │       └── endpoints/
│   │           ├── auth.py         ← POST /auth/login
│   │           ├── users.py        ← CRUD /users
│   │           └── health.py       ← GET /health
│   │
│   ├── middleware/
│   │   └── logging.py              ← Per-request logging
│   │
│   └── exceptions/
│       └── handlers.py             ← Global 422 and 500 handlers
│
├── tests/
│   ├── conftest.py                 ← SQLite DB + TestClient fixtures
│   ├── api/v1/
│   │   ├── test_auth.py
│   │   └── test_users.py
│   └── unit/
│       └── test_security.py
│
├── alembic/                        ← Database migration scripts
│   ├── env.py                      ← Migration runner (reads settings.DATABASE_URL)
│   ├── script.py.mako              ← Template for new migration files
│   └── versions/                   ← Auto-generated migration files
│
├── docs/                           ← Project documentation
│   └── project_structure.md        ← This file
│
├── .env                            ← Local secrets (not committed)
├── .env.example                    ← Template — copy to .env
├── alembic.ini                     ← Alembic config (script_location, logging)
├── pyproject.toml                  ← black / isort / pytest config
├── requirements.txt                ← Production dependencies
├── requirements-dev.txt            ← Dev + test dependencies
├── Dockerfile
└── docker-compose.yml
```

---

## app/main.py — App Factory

**Purpose:** Creates and configures the FastAPI application instance.

**What it does (in order):**
1. Defines a `lifespan` context manager (startup / shutdown hooks go here)
2. Creates the `FastAPI` app with title, version, and OpenAPI URL from `settings`
3. Conditionally adds `CORSMiddleware` if `BACKEND_CORS_ORIGINS` is set in `.env`
4. Adds `RequestLoggingMiddleware` (logs every request)
5. Registers global exception handlers (422 validation, 500 unhandled)
6. Mounts `api_router` which contains all routes

**Exports:** `app` — the ASGI application, used by `uvicorn app.main:app`

---

## app/core/

### config.py — Settings

**Purpose:** Single source of truth for all environment configuration.

**How it works:**
- Uses Pydantic `BaseSettings` — fields are automatically populated from `.env`
- `case_sensitive=True` means `.env` keys must match exactly (uppercase)
- Instantiates a module-level singleton `settings` — always import this, never `os.getenv`

**Fields:**

| Field | Default | Description |
|-------|---------|-------------|
| `PROJECT_NAME` | `"FastAPI App"` | Shown in Swagger UI title |
| `VERSION` | `"1.0.0"` | API version string |
| `API_V1_STR` | `"/api/v1"` | URL prefix for all v1 routes |
| `DEBUG` | `false` | Debug mode toggle |
| `DATABASE_URL` | postgres default | Full SQLAlchemy connection string |
| `SECRET_KEY` | placeholder | Signs JWT tokens — must be changed in production |
| `ALGORITHM` | `"HS256"` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |
| `BACKEND_CORS_ORIGINS` | `[]` | List of allowed CORS origins |

---

### database.py — Database Session

**Purpose:** Sets up the SQLAlchemy engine, session factory, ORM base class, and the `get_db` dependency.

**Key exports:**

| Export | Type | Used by |
|--------|------|---------|
| `engine` | `Engine` | Alembic `env.py` |
| `SessionLocal` | `sessionmaker` | `get_db`, test `conftest.py` |
| `Base` | `DeclarativeBase` | All ORM models inherit from this |
| `get_db` | generator function | FastAPI `Depends(get_db)` in endpoints |

**How `get_db` works:**
```
Request arrives
  → get_db() opens a SessionLocal
  → yields the session to the endpoint
  → endpoint runs (reads/writes DB)
  → finally block closes the session (even on exception)
```

`pool_pre_ping=True` — SQLAlchemy tests the connection before using it, preventing stale connection errors after DB restarts.

---

### security.py — JWT & Password Hashing

**Purpose:** All cryptographic operations — token creation, token verification, password hashing.

**Key exports:**

| Function | Input | Output | Used by |
|----------|-------|--------|---------|
| `create_access_token(subject, expires_delta)` | user ID | signed JWT string | `auth.py` login endpoint |
| `verify_password(plain, hashed)` | two strings | `bool` | `user_service.authenticate` |
| `get_password_hash(password)` | plain string | bcrypt hash | `user_service.create/update` |

**Token payload structure:**
```json
{
  "sub": "1",           ← user ID as string
  "exp": 1234567890     ← UTC timestamp (now + ACCESS_TOKEN_EXPIRE_MINUTES)
}
```

**bcrypt note:** Requires `bcrypt==4.0.1` — bcrypt 5.x removed the `__about__` attribute that passlib 1.7.4 depends on for version detection. The pin is in `requirements.txt`.

---

### deps.py — FastAPI Dependencies

**Purpose:** Reusable FastAPI `Depends()` functions for authentication and authorization.

**Dependency chain:**

```
oauth2_scheme          → extracts Bearer token from Authorization header
    ↓
get_current_user       → decodes JWT → loads User from DB
    ↓
get_current_active_user → checks user.is_active == True
    ↓
get_current_superuser  → checks user.is_superuser == True
```

Each step raises `HTTPException` if the check fails:

| Dependency | Failure response |
|-----------|-----------------|
| `get_current_user` | 401 — invalid/missing token |
| `get_current_active_user` | 400 — user is deactivated |
| `get_current_superuser` | 403 — user is not superuser |

---

## app/models/

### user.py — User ORM Model

**Table:** `users`

**Columns:**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | Primary key, indexed |
| `email` | String | Unique, indexed, not null |
| `hashed_password` | String | Not null (never stores plain text) |
| `full_name` | String | Nullable |
| `is_active` | Boolean | Default `True` |
| `is_superuser` | Boolean | Default `False` — controls admin access |
| `created_at` | DateTime (tz) | Auto-set on insert |
| `updated_at` | DateTime (tz) | Auto-set on insert and update |

### \_\_init\_\_.py

Imports `User` so Alembic's `env.py` can discover all models via `Base.metadata` during autogenerate. **Always add new model imports here.**

---

## app/schemas/

Pydantic v2 schemas — used for request body validation and response serialization. Never used for DB queries (that's the model's job).

### user.py

| Class | Inherits | Purpose |
|-------|----------|---------|
| `UserBase` | `BaseModel` | Shared fields: `email`, `full_name` |
| `UserCreate` | `UserBase` | Registration input — adds `password` |
| `UserUpdate` | `BaseModel` | Partial update — all fields optional |
| `UserResponse` | `UserBase` | API response — adds `id`, `is_active`, `is_superuser`; `from_attributes=True` enables ORM→schema conversion |

### token.py

| Class | Fields | Purpose |
|-------|--------|---------|
| `Token` | `access_token`, `token_type="bearer"` | Login response body |
| `TokenData` | `user_id: int` | Internal — holds decoded JWT payload |

---

## app/repositories/

The repository layer owns all SQLAlchemy queries. No business logic, no `HTTPException` — just DB reads and writes.

### base.py — BaseRepository

Generic class parameterized by `ModelType`:

| Method | SQL equivalent | Returns |
|--------|---------------|---------|
| `get(db, id)` | `SELECT WHERE id=?` | `ModelType \| None` |
| `get_multi(db, skip, limit)` | `SELECT LIMIT OFFSET` | `list[ModelType]` |
| `create(db, obj_in)` | `INSERT` | `ModelType` (refreshed) |
| `update(db, db_obj, obj_in)` | `UPDATE` | `ModelType` (refreshed) |
| `delete(db, id)` | `DELETE WHERE id=?` | `ModelType \| None` |

### user_repository.py

Extends `BaseRepository[User]` with user-specific queries:

| Method | Purpose |
|--------|---------|
| `get_by_email(db, email)` | Used by login to find user |
| `email_exists(db, email)` | Used by registration to check for duplicates |

Exports a module-level singleton `user_repository = UserRepository(User)`.

---

## app/services/

The service layer holds business logic. It calls repositories and raises `HTTPException` when business rules are violated. Endpoints call services; services never call endpoints.

### user_service.py — UserService

| Method | Business logic |
|--------|---------------|
| `get_by_id` | Raises 404 if user not found |
| `get_all` | Returns paginated user list |
| `create` | Checks email uniqueness → hashes password → creates user |
| `update` | Handles optional password re-hash during update |
| `delete` | Raises 404 if user not found |
| `authenticate` | Looks up by email → bcrypt verify → returns `None` on failure (never raises) |

Exports a module-level singleton `user_service = UserService()`.

---

## app/api/

### api_router.py

Mounts the v1 router with the `API_V1_STR` prefix from settings (`/api/v1`). This is the only router imported by `main.py`.

### v1/router.py

Aggregates all endpoint routers under `v1`:

| Router | Prefix | Tags |
|--------|--------|------|
| `health.router` | `/health` | `health` |
| `auth.router` | `/auth` | `auth` |
| `users.router` | `/users` | `users` |

### v1/endpoints/health.py

Single endpoint: `GET /api/v1/health` — no auth, returns `{"status": "ok"}`. Used for load balancer health checks.

### v1/endpoints/auth.py

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Accepts `OAuth2PasswordRequestForm` (form data: `username`, `password`) → returns `Token` |

**Login flow:**
```
form_data.username (email) + form_data.password
  → user_service.authenticate()
  → verify_password() with bcrypt
  → create_access_token(user.id)
  → return Token { access_token, token_type: "bearer" }
```

> Login uses **form data** (`Content-Type: multipart/form-data`), not JSON — required by the OAuth2 spec that `OAuth2PasswordRequestForm` implements.

### v1/endpoints/users.py

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/users` | None | Register new user → 201 |
| GET | `/users/me` | Bearer | Current user profile |
| PATCH | `/users/me` | Bearer | Update own profile |
| GET | `/users` | Superuser | List all users |
| GET | `/users/{user_id}` | Superuser | Get user by ID |
| DELETE | `/users/{user_id}` | Superuser | Delete user by ID |

---

## app/middleware/logging.py — RequestLoggingMiddleware

Wraps every request with a timer. Prints to stdout after the response is sent:

```
GET /api/v1/users/me status=200 duration=0.012s
```

Extends Starlette's `BaseHTTPMiddleware` — registered in `main.py` via `app.add_middleware()`.

---

## app/exceptions/handlers.py — Global Exception Handlers

| Handler | Triggered by | HTTP status | Response body |
|---------|-------------|-------------|---------------|
| `validation_exception_handler` | Pydantic validation failure (wrong field types, missing required fields) | 422 | `{detail: [...errors], body: ...}` |
| `unhandled_exception_handler` | Any unhandled Python exception | 500 | `{detail: "Internal server error"}` |

Both registered in `main.py`. The 500 handler deliberately hides internal error details from clients — check server stdout for the real traceback.

---

## tests/

### conftest.py — Test Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `setup_db` | session | Creates all tables in SQLite before tests run; drops them after |
| `db` | function | Opens a `TestingSessionLocal` session; **rolls back** after each test to isolate state |
| `client` | function | Overrides `get_db` dependency to use the test SQLite session; returns a `TestClient` |

**Why SQLite?** No PostgreSQL install required to run tests. SQLite supports the same SQLAlchemy ORM syntax used in production.

**Important:** The `db` fixture rolls back — not commits — so each test starts with a clean slate even if it inserts data.

### tests/api/v1/ — Integration Tests

Test HTTP endpoints end-to-end through the full stack (routing → service → repository → SQLite).

| File | Tests |
|------|-------|
| `test_auth.py` | Invalid login returns 401; register + login returns token |
| `test_users.py` | Unauthenticated `/me` returns 401; register → login → `/me` returns profile; duplicate email returns 400 |

### tests/unit/ — Unit Tests

Test pure functions in isolation, no HTTP or DB.

| File | Tests |
|------|-------|
| `test_security.py` | Password hash is not plain text; verify works; wrong password fails; `create_access_token` returns a non-empty string |

---

## alembic/

### env.py — Migration Runner

- Reads `DATABASE_URL` from `settings` (not from `alembic.ini`)
- Imports `app.models` to register all models with `Base.metadata`
- Supports both **offline** mode (generates SQL) and **online** mode (runs against live DB)

### script.py.mako — Migration Template

Mako template used by `alembic revision --autogenerate` to generate new migration files in `versions/`. Each generated file has `upgrade()` and `downgrade()` functions.

### versions/

Auto-generated migration files. Each file is named `<rev_id>_<message>.py` and tracks schema changes as Python code. Committed to git — they are the source of truth for DB schema history.

---

## Configuration Files

### .env / .env.example

`.env` is never committed (in `.gitignore`). `.env.example` is the template:

```env
DATABASE_URL=postgresql://<user>@localhost:5432/fastapi_db
SECRET_KEY=<long-random-string>
DEBUG=false
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### pyproject.toml

```toml
[tool.black]       line-length = 100
[tool.isort]       profile = "black", line_length = 100
[tool.pytest]      testpaths = ["tests"]
[tool.coverage]    source = ["app"]
```

### requirements.txt vs requirements-dev.txt

`requirements.txt` — production only (no test/lint tools).  
`requirements-dev.txt` starts with `-r requirements.txt` then adds: `pytest`, `pytest-cov`, `httpx`, `black`, `isort`, `flake8`.

---

## Data Flow Diagrams

### Register → Login → Authenticated Request

```
POST /api/v1/users
  Body: { email, password }
  → UserCreate schema validates input
  → user_service.create()
      → email_exists check (400 if duplicate)
      → get_password_hash(password)  ← bcrypt
      → user_repository.create()     ← INSERT INTO users
  ← 201 UserResponse { id, email, is_active, is_superuser }

POST /api/v1/auth/login
  Form: username=email, password=plain
  → user_service.authenticate()
      → user_repository.get_by_email()   ← SELECT WHERE email=?
      → verify_password(plain, hashed)   ← bcrypt.verify
  → create_access_token(user.id)         ← JWT signed with SECRET_KEY
  ← 200 Token { access_token, token_type }

GET /api/v1/users/me
  Header: Authorization: Bearer <token>
  → oauth2_scheme extracts token
  → get_current_user dep
      → jwt.decode(token, SECRET_KEY)    ← verifies signature + expiry
      → db.get(User, user_id)            ← SELECT WHERE id=?
  → get_current_active_user dep
      → checks user.is_active
  ← 200 UserResponse
```

### Adding a New Resource (Pattern)

```
1. app/models/product.py          ← SQLAlchemy model, inherits Base
2. app/models/__init__.py         ← add: from app.models.product import Product
3. app/schemas/product.py         ← ProductCreate, ProductUpdate, ProductResponse
4. app/repositories/product_repository.py  ← extends BaseRepository[Product]
5. app/services/product_service.py         ← business logic, uses repository
6. app/api/v1/endpoints/products.py        ← APIRouter with route handlers
7. app/api/v1/router.py           ← include products.router
8. alembic revision --autogenerate -m "add products"
9. alembic upgrade head
```

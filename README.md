# FastAPI App

A production-ready REST API built with FastAPI, PostgreSQL, SQLAlchemy, JWT authentication, and a clean layered architecture (Repository → Service → Endpoint).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2.x ORM |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v2 |
| Testing | pytest + SQLite (in-memory) |

---

## Project Structure

```
fastapi-app/
├── app/
│   ├── main.py                        # App factory, middleware, exception handlers
│   ├── core/
│   │   ├── config.py                  # All settings loaded from .env
│   │   ├── database.py                # SQLAlchemy engine, Base, get_db
│   │   ├── security.py                # JWT creation, password hashing
│   │   └── deps.py                    # FastAPI dependencies (current user, auth guards)
│   ├── models/                        # SQLAlchemy ORM models
│   ├── schemas/                       # Pydantic request/response schemas
│   ├── repositories/                  # Raw DB queries (generic BaseRepository + per-model)
│   ├── services/                      # Business logic, raises HTTPException
│   ├── api/v1/endpoints/              # Route handlers (auth, users, health)
│   ├── middleware/logging.py          # Logs method, path, status, duration per request
│   └── exceptions/handlers.py        # Global 422 and 500 handlers
├── tests/
│   ├── conftest.py                    # SQLite test DB + TestClient fixture
│   ├── api/v1/                        # Integration tests
│   └── unit/                         # Unit tests
├── alembic/                           # Migration scripts
├── .env                               # Local environment variables (not committed)
├── .env.example                       # Template for .env
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt               # Dev + test dependencies
├── pyproject.toml                     # black / isort / pytest config
├── Dockerfile
└── docker-compose.yml
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL running locally

### 1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
DATABASE_URL=postgresql://<your-pg-user>@localhost:5432/fastapi_db
SECRET_KEY=your-long-random-secret-key
DEBUG=false
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Create the database

```bash
psql -h localhost -U <your-pg-user> -d postgres -c "CREATE DATABASE fastapi_db;"
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

---

## Docker Setup (Alternative)

Runs the app + PostgreSQL together — no local Postgres needed.

```bash
cp .env.example .env
docker-compose up --build
```

Then apply migrations:

```bash
docker-compose exec app alembic upgrade head
```

---

## API Overview

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | None | Login, returns JWT token |

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/users` | None | Register a new user |
| GET | `/users/me` | Bearer token | Get current user profile |
| PATCH | `/users/me` | Bearer token | Update current user profile |
| GET | `/users` | Superuser | List all users |
| GET | `/users/{id}` | Superuser | Get user by ID |
| DELETE | `/users/{id}` | Superuser | Delete user by ID |

---

## Request Flow

```
HTTP Request
    │
    ▼
main.py  ──►  RequestLoggingMiddleware  ──►  CORSMiddleware
    │
    ▼
api/v1/endpoints/*.py       ← handles HTTP, validates input via Pydantic schema
    │
    ├── Depends(get_db)      ← injects SQLAlchemy session
    ├── Depends(get_current_user)  ← decodes JWT → loads User from DB
    │
    ▼
services/                   ← business logic, raises HTTPException on errors
    │
    ▼
repositories/               ← executes DB queries via SQLAlchemy ORM
    │
    ▼
PostgreSQL
```

### Auth Flow

```
POST /api/v1/auth/login
  form: username=email, password=plain

  1. user_service.authenticate() → looks up user by email
  2. verify_password() → bcrypt compare
  3. create_access_token() → signed JWT (HS256), expires in 30 min
  4. Returns: { "access_token": "...", "token_type": "bearer" }

Subsequent requests:
  Header: Authorization: Bearer <token>
  → get_current_user dep decodes JWT → fetches User → injects into endpoint
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Single test
pytest tests/api/v1/test_auth.py::test_register_and_login -v
```

Tests use SQLite (`test.db`) — no PostgreSQL required. The `db` fixture rolls back after each test to keep tests isolated.

---

## Adding a New Resource

1. **Model** — add `app/models/<name>.py`, import it in `app/models/__init__.py`
2. **Schema** — add `app/schemas/<name>.py` (Base / Create / Update / Response)
3. **Repository** — add `app/repositories/<name>_repository.py` extending `BaseRepository`
4. **Service** — add `app/services/<name>_service.py` with business logic
5. **Endpoint** — add `app/api/v1/endpoints/<name>.py` with an `APIRouter`
6. **Register** — include the router in `app/api/v1/router.py`
7. **Migrate** — run `alembic revision --autogenerate -m "add <name>"` then `alembic upgrade head`

---

## Code Style

```bash
black app/       # format
isort app/       # sort imports
flake8 app/      # lint
```

Line length: 100. Config in `pyproject.toml`.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the dev server:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

**Run tests:**
```bash
source venv/bin/activate
pytest
```

**Run a single test:**
```bash
pytest tests/path/to/test_file.py::test_function_name -v
```

**Run tests with coverage:**
```bash
pytest --cov=app --cov-report=term-missing
```

**Lint and format:**
```bash
flake8 app/
black app/
isort app/
```

**Database migrations (Alembic):**
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

**Install dependencies:**
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

**Docker:**
```bash
docker-compose up --build
```

## Architecture

Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2.x ORM, PostgreSQL via psycopg2, Pydantic v2, JWT auth via python-jose + passlib[bcrypt], Alembic migrations.

### Layer overview

```
app/
├── main.py               # App factory: mounts middleware, exception handlers, api_router
├── core/
│   ├── config.py         # Pydantic BaseSettings — all env vars loaded from .env
│   ├── database.py       # SQLAlchemy engine, SessionLocal, Base, get_db generator
│   ├── security.py       # JWT create/decode, password hash/verify (passlib bcrypt)
│   └── deps.py           # FastAPI dependencies: get_current_user, get_current_active_user,
│                         #   get_current_superuser — all built on oauth2_scheme
├── models/               # SQLAlchemy ORM models (import all in __init__.py for Alembic)
├── schemas/              # Pydantic v2 request/response schemas
├── repositories/
│   ├── base.py           # Generic BaseRepository[ModelType] with get/get_multi/create/update/delete
│   └── *_repository.py   # Per-model repos extending BaseRepository; singleton exported
├── services/             # Business logic; raise HTTPException; call repositories
├── api/
│   ├── api_router.py     # Mounts v1_router at settings.API_V1_STR (/api/v1)
│   └── v1/
│       ├── router.py     # Aggregates all v1 endpoint routers
│       └── endpoints/    # One file per resource (auth, users, health)
├── middleware/
│   └── logging.py        # RequestLoggingMiddleware prints method/path/status/duration
└── exceptions/
    └── handlers.py       # validation_exception_handler + unhandled_exception_handler
tests/
├── conftest.py           # SQLite test DB, db fixture (with rollback), client fixture
├── api/v1/               # Integration tests via TestClient
└── unit/                 # Unit tests (no DB)
alembic/
└── env.py                # Reads DATABASE_URL from settings; imports app.models for autogenerate
```

### Key conventions

- **Config access**: always import `settings` from `app.core.config`; never use `os.getenv` directly.
- **DB session**: injected via `Depends(get_db)`; never instantiate `SessionLocal` manually outside tests.
- **Auth flow**: `POST /api/v1/auth/login` → JWT → `Authorization: Bearer <token>` → `get_current_user` dep resolves the `User` model.
- **Adding a new resource**: create model → schema → repository (extend `BaseRepository`) → service → endpoint router → register in `app/api/v1/router.py` → add model import to `app/models/__init__.py`.
- **Alembic autogenerate**: `app/models/__init__.py` imports all models so `alembic/env.py` picks them up via `Base.metadata`.
- **Tests use SQLite** (`test.db`) with `TestClient`; the `db` fixture rolls back after each test; `setup_db` is session-scoped.

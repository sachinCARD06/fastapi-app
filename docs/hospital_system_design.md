# Hospital System Design

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Model](#data-model)
4. [API Endpoints](#api-endpoints)
5. [Request Flow Diagrams](#request-flow-diagrams)
6. [Auth & Authorization](#auth--authorization)
7. [CRUD Operation Flows](#crud-operation-flows)
8. [Error Handling](#error-handling)
9. [Layer Responsibilities](#layer-responsibilities)

---

## Overview

The Hospital module is a CRUD resource in the FastAPI app. It allows authenticated users to list hospitals and superusers to manage (create / update / delete) them. Hospitals are uniquely identified by name, belong to a PostgreSQL table with audit columns (`created_by`, `updated_by`), and eagerly load their associated `User` records for every response.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client / HTTP                    │
└────────────────────────┬────────────────────────────┘
                         │  HTTP Request
                         ▼
┌─────────────────────────────────────────────────────┐
│               FastAPI Application                   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │       Middleware (RequestLoggingMiddleware)  │   │
│  └────────────────────┬─────────────────────────┘   │
│                       │                             │
│  ┌────────────────────▼─────────────────────────┐   │
│  │         api_router  /api/v1                  │   │
│  │                                              │   │
│  │   ┌──────────────────────────────────────┐   │   │
│  │   │  /api/v1/hospitals  (router.py)      │   │   │
│  │   │  endpoints/hospitals.py              │   │   │
│  │   └──────────────┬───────────────────────┘   │   │
│  └──────────────────│──────────────────────────-┘   │
│                     │                               │
│  ┌──────────────────▼──────────────────────────┐    │
│  │  FastAPI Dependencies                       │    │
│  │  • get_db          → SQLAlchemy Session     │    │
│  │  • get_current_active_user  → User model    │    │
│  │  • get_current_superuser    → User model    │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                               │
│  ┌──────────────────▼──────────────────────────┐    │
│  │           HospitalService                   │    │
│  │  Business logic, validation, HTTPExceptions │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                               │
│  ┌──────────────────▼──────────────────────────┐    │
│  │         HospitalRepository                  │    │
│  │  (extends BaseRepository[Hospital])         │    │
│  │  get / get_multi / get_active / name_exists │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │  SQLAlchemy ORM               │
│  ┌──────────────────▼──────────────────────────┐    │
│  │           Hospital (ORM Model)              │    │
│  └──────────────────┬──────────────────────────┘    │
└─────────────────────│───────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │     PostgreSQL DB      │
         │   table: hospitals     │
         └────────────────────────┘
```

---

## Data Model

### Database Table: `hospitals`

```
┌──────────────────────────────────────────────────────────────┐
│                         hospitals                            │
├────────────────┬──────────────────┬──────────────────────────┤
│ Column         │ Type             │ Constraints              │
├────────────────┼──────────────────┼──────────────────────────┤
│ id             │ INTEGER          │ PK, autoincrement, index │
│ name           │ VARCHAR          │ NOT NULL, UNIQUE, index  │
│ address        │ VARCHAR          │ NOT NULL                 │
│ city           │ VARCHAR          │ NOT NULL                 │
│ mobile_number  │ VARCHAR          │ NOT NULL                 │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ created_by     │ INTEGER          │ FK → users.id, nullable  │
│ updated_by     │ INTEGER          │ FK → users.id, nullable  │
│ created_at     │ TIMESTAMPTZ      │ default NOW()            │
│ updated_at     │ TIMESTAMPTZ      │ default NOW(), on update │
└────────────────┴──────────────────┴──────────────────────────┘
```

### Relationships

```
┌──────────────┐       ┌───────────────────┐
│    users     │       │     hospitals     │
├──────────────┤       ├───────────────────┤
│ id  (PK)     │◄──────│ created_by (FK)   │
│ email        │       │ updated_by (FK)   │
│ full_name    │◄──────│                   │
│ ...          │       │                   │
└──────────────┘       └───────────────────┘
  User.creator  ←→  Hospital.creator  (foreign_keys=[created_by])
  User.updater  ←→  Hospital.updater  (foreign_keys=[updated_by])
```

### Schema Layers (Pydantic)

```
HospitalBase          ← name, address, city, mobile_number
    │
    ├── HospitalCreate    (used for POST body — no extra fields)
    │
    └── HospitalResponse  ← + id, is_active, created_by, updated_by,
                              creator: UserBrief, updater: UserBrief

HospitalUpdate        ← all fields optional + is_active (PATCH body)

UserBrief             ← id, email, full_name  (nested in response)
```

---

## API Endpoints

| Method   | Path                        | Auth Required    | Description                   |
|----------|-----------------------------|------------------|-------------------------------|
| `GET`    | `/api/v1/hospitals`         | active user      | List all hospitals (paginated)|
| `GET`    | `/api/v1/hospitals/active`  | active user      | List only active hospitals    |
| `POST`   | `/api/v1/hospitals`         | superuser only   | Create a new hospital         |
| `GET`    | `/api/v1/hospitals/{id}`    | active user      | Fetch a single hospital       |
| `PATCH`  | `/api/v1/hospitals/{id}`    | superuser only   | Partial update a hospital     |
| `DELETE` | `/api/v1/hospitals/{id}`    | superuser only   | Delete a hospital             |

Query params for list endpoints: `?skip=0&limit=100`

---

## Request Flow Diagrams

### Generic Request Flow

```
Client
  │
  │  GET/POST/PATCH/DELETE /api/v1/hospitals/...
  ▼
RequestLoggingMiddleware
  │  logs: method, path, status, duration
  ▼
FastAPI Router  (app/api/v1/router.py)
  │
  ▼
Endpoint Function  (app/api/v1/endpoints/hospitals.py)
  │
  ├─► Depends(get_db)              → open SQLAlchemy session
  │
  ├─► Depends(get_current_active_user)   ─┐
  │   OR                                  │  JWT decode → load User from DB
  └─► Depends(get_current_superuser)     ─┘
           │
           │ if token invalid or insufficient role → 401/403
           │
           ▼
  HospitalService  (app/services/hospital_service.py)
           │
           ├─ business validation (name uniqueness, existence check)
           │  if fails → raise HTTPException 400/404
           │
           ▼
  HospitalRepository  (app/repositories/hospital_repository.py)
           │
           ├─ SQLAlchemy query with joinedload(creator, updater)
           │
           ▼
  PostgreSQL DB
           │
           ▼
  Hospital ORM Model  →  HospitalResponse (Pydantic serialization)
           │
           ▼
Client  ← JSON Response
```

---

## Auth & Authorization

```
POST /api/v1/auth/login
  │
  │  { email, password }
  ▼
AuthService verifies password (bcrypt)
  │
  ▼
JWT token created  { sub: user_id, exp: ... }
  │
  ▼
Client stores Bearer token

─────────────────────────────────────────────────

Subsequent request to /api/v1/hospitals/...
  │
  │  Header: Authorization: Bearer <token>
  ▼
oauth2_scheme extracts token
  │
  ▼
security.decode_token()  →  payload
  │
  ▼
UserRepository.get(payload["sub"])  →  User model
  │
  ├─ get_current_active_user:  check user.is_active  →  403 if inactive
  │
  └─ get_current_superuser:    check user.is_superuser → 403 if not super
```

**Role matrix:**

```
                    │  Anonymous │  Active User │  Superuser
────────────────────┼────────────┼──────────────┼───────────
GET  /hospitals     │    401     │     ✓        │     ✓
GET  /hospitals/id  │    401     │     ✓        │     ✓
GET  /active        │    401     │     ✓        │     ✓
POST /hospitals     │    401     │    403       │     ✓
PATCH /hospitals/id │    401     │    403       │     ✓
DELETE/hospitals/id │    401     │    403       │     ✓
```

---

## CRUD Operation Flows

### Create Hospital  `POST /api/v1/hospitals`

```
Client  →  POST /api/v1/hospitals
            body: { name, address, city, mobile_number }
            header: Bearer <superuser token>
                │
                ▼
       get_current_superuser dep
                │
                ▼
       HospitalService.create()
                │
                ├─ hospital_repository.name_exists(name)
                │       │
                │       ├─ True  →  HTTP 400 "Hospital with this name already exists"
                │       │
                │       └─ False ↓
                │
                ▼
       hospital_repository.create(
           { ...hospital_in, created_by: current_user.id }
       )
                │
                ├─ INSERT INTO hospitals (...)
                ├─ db.commit()
                ├─ db.refresh()  →  return Hospital ORM
                │
                ▼
       HTTP 201  →  HospitalResponse JSON
```

### Read Hospital  `GET /api/v1/hospitals/{id}`

```
Client  →  GET /api/v1/hospitals/42
            header: Bearer <active user token>
                │
                ▼
       get_current_active_user dep
                │
                ▼
       HospitalService.get_by_id(42)
                │
                ▼
       hospital_repository.get(db, 42)
                │
                ├─ SELECT hospitals JOIN users (creator) JOIN users (updater)
                │  WHERE hospitals.id = 42
                │
                ├─ None  →  HTTP 404 "Hospital not found"
                │
                └─ Hospital ORM  →  HTTP 200  →  HospitalResponse JSON
```

### List Hospitals  `GET /api/v1/hospitals`

```
Client  →  GET /api/v1/hospitals?skip=0&limit=20
                │
                ▼
       get_current_active_user dep
                │
                ▼
       HospitalService.get_all(skip=0, limit=20)
                │
                ▼
       hospital_repository.get_multi(skip=0, limit=20)
                │
                ├─ SELECT ... FROM hospitals
                │  LEFT JOIN users AS creator ON ...
                │  LEFT JOIN users AS updater ON ...
                │  OFFSET 0 LIMIT 20
                │
                └─ list[Hospital]  →  HTTP 200  →  list[HospitalResponse] JSON
```

### List Active Hospitals  `GET /api/v1/hospitals/active`

```
       hospital_repository.get_active()
                │
                ├─ same as get_multi +
                │  WHERE hospitals.is_active = TRUE
                │
                └─ list[Hospital]  →  HTTP 200
```

### Update Hospital  `PATCH /api/v1/hospitals/{id}`

```
Client  →  PATCH /api/v1/hospitals/42
            body: { city: "Mumbai", is_active: false }   ← partial, all optional
            header: Bearer <superuser token>
                │
                ▼
       get_current_superuser dep
                │
                ▼
       HospitalService.update(42, hospital_in, updated_by=current_user.id)
                │
                ├─ get_by_id(42)  →  404 if not found
                │
                ├─ model_dump(exclude_none=True)  →  only provided fields
                │
                ├─ if "name" in update_data AND name changed:
                │       hospital_repository.name_exists(new_name)
                │       True  →  HTTP 400 "name already exists"
                │
                ├─ update_data["updated_by"] = current_user.id
                │
                ▼
       hospital_repository.update(db_obj=hospital, obj_in=update_data)
                │
                ├─ setattr(hospital, field, value)  for each field
                ├─ db.commit()
                └─ db.refresh()  →  return updated Hospital ORM
                │
                ▼
       HTTP 200  →  HospitalResponse JSON
```

### Delete Hospital  `DELETE /api/v1/hospitals/{id}`

```
Client  →  DELETE /api/v1/hospitals/42
            header: Bearer <superuser token>
                │
                ▼
       get_current_superuser dep
                │
                ▼
       HospitalService.delete(42)
                │
                ▼
       hospital_repository.delete(id=42)
                │
                ├─ db.get(Hospital, 42)
                │
                ├─ None  →  HTTP 404 "Hospital not found"
                │
                ├─ db.delete(obj)
                └─ db.commit()  →  return deleted Hospital ORM
                │
                ▼
       HTTP 200  →  HospitalResponse JSON  (snapshot of deleted record)
```

---

## Error Handling

| Scenario                          | HTTP Status | Detail                                    |
|-----------------------------------|-------------|-------------------------------------------|
| Missing / invalid JWT token       | 401         | "Could not validate credentials"          |
| Inactive user                     | 403         | "Inactive user"                           |
| Non-superuser on write endpoint   | 403         | "The user doesn't have enough privileges" |
| Hospital not found (get/update)   | 404         | "Hospital not found"                      |
| Hospital not found (delete)       | 404         | "Hospital not found"                      |
| Duplicate hospital name           | 400         | "Hospital with this name already exists"  |
| Validation error (bad body)       | 422         | Pydantic field errors                     |
| Unhandled server error            | 500         | "Internal Server Error"                   |

---

## Layer Responsibilities

```
┌─────────────────────┬──────────────────────────────────────────────────┐
│ Layer               │ Responsibility                                   │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Endpoint            │ HTTP in/out, dependency injection, status codes  │
│ (hospitals.py)      │ No business logic                                │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Service             │ Business rules: uniqueness checks, existence     │
│ (hospital_service)  │ checks, audit field injection. Raises HTTP       │
│                     │ exceptions. Orchestrates repository calls.       │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Repository          │ Pure DB access. Builds SQLAlchemy queries,       │
│ (hospital_repo)     │ eager-loads relationships, commits transactions. │
│                     │ Extends generic BaseRepository[Hospital].        │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Model               │ ORM mapping, column definitions, FK relationships│
│ (Hospital)          │ No business logic                                │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Schema              │ Input validation (Pydantic), response shaping,   │
│ (hospital.py)       │ UserBrief nesting in responses                   │
└─────────────────────┴──────────────────────────────────────────────────┘
```

### Eager Loading Strategy

All read queries use `joinedload` to prevent N+1 queries:

```python
query.options(
    joinedload(Hospital.creator),   # fetches User for created_by in same SQL
    joinedload(Hospital.updater),   # fetches User for updated_by in same SQL
)
```

This means every `HospitalResponse` has `creator` and `updater` fully populated without additional round-trips to the DB.

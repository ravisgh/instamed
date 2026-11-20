# InstaMed Backend

Pharmacy backend built with **FastAPI** and **MongoDB** (async, via Motor).
It manages medicines, stores, inventory and pincode-to-warehouse zones, and
answers "is this medicine available at my pincode?".

## Tech stack

| Layer | Tool |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Database | MongoDB via Motor (async driver) |
| Validation / config | Pydantic v2, pydantic-settings |
| Tests / lint | pytest + httpx, ruff |

## Project layout

```
app/
├── main.py          # FastAPI app, registers routers
├── db.py            # Mongo client opened in lifespan, get_db dependency, indexes
├── core/
│   ├── config.py    # Settings loaded from env / .env
│   ├── crud.py      # Shared insert/list/get/update/delete with 404/409 handling
│   ├── ids.py       # ObjectId parsing and validation
│   └── pagination.py
├── models/          # Pydantic Create / Update / Out schemas per resource
└── routes/          # API endpoints, one file per resource
tests/               # pytest tests
```

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env   # then edit .env with your MongoDB details
```

You need a running MongoDB (local or Atlas) for the data endpoints.

## Run

```powershell
uvicorn app.main:app --reload
```

Interactive API docs: http://127.0.0.1:8000/docs

## Test and lint

```powershell
pytest
ruff check .
```

Tests need a **local** MongoDB on `localhost:27017`. They always use a throwaway
database named `instamed_test`, which is dropped after each test. `tests/conftest.py`
aborts the run if settings point at any other host or database, so tests can never
touch Atlas or your other local databases.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `instamed` | Database name |

## Endpoints

`medicines`, `stores`, `inventory` and `pincode-zones` all follow the same shape:

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/{resource}` | 201 + created item | 422 invalid body, 404 referenced id missing, 409 duplicate |
| GET | `/{resource}?skip=0&limit=20` | 200 list (limit 1-100) | 422 bad paging |
| GET | `/{resource}/{id}` | 200 item | 400 malformed id, 404 |
| PATCH | `/{resource}/{id}` | 200 updated item | 400, 404, 409, 422 (empty or invalid body) |
| DELETE | `/{resource}/{id}` | 204 | 400, 404 |

Other endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health message |
| GET | `/test-db` | List collections (dev only, removed in Phase 3) |
| GET | `/search?pincode=&medicine_name=` | Price and stock of a medicine for a pincode (name is case-insensitive) |

Rules worth knowing:
- One inventory row per (store, medicine); one zone per pincode.
- Inventory `medicine_id`/`store_id` and zone `warehouse_id` must point at existing documents.
- Pincodes are 6-digit Indian PINs (first digit 1-9).

### Breaking changes in v0.2.0
- `PUT /medicines/{id}` is now `PATCH` (send only the fields to change).
- `POST /pincode_zone` and `GET /pincode-zone` are now `/pincode-zones`.
- Errors return proper HTTP status codes with `{"detail": "..."}` instead of `200 {"error": "..."}`.

## Roadmap

- [x] Phase 0: Foundation (config, tests, lint, docs)
- [x] Phase 1: Correctness (status codes, validation, pagination, full CRUD)
- [ ] Phase 2: Layered architecture, logging, indexes
- [ ] Phase 3: Authentication and roles (JWT)
- [ ] Phase 4: Orders, cart, prescriptions, atomic stock updates
- [ ] Phase 5: Elasticsearch medicine search
- [ ] Phase 6: Docker, CI, pre-commit

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
│   ├── ids.py       # ObjectId parsing and validation
│   ├── logging.py   # Logger setup; every line carries the request id
│   ├── middleware.py  # X-Request-ID, access log, JSON 500 handler
│   └── pagination.py
├── importers/evital.py  # Cleans eVital stock exports into medicines + inventory
├── models/          # Pydantic Create / Update / Out schemas per resource
├── repositories/    # Data access: one MongoRepository per collection (404/409 handling)
├── services/        # Business rules spanning collections (reference checks, search)
└── routes/          # Thin HTTP layer: validate input, call a service or repository
scripts/seed_evital.py   # CLI: load an eVital export into a local dev database
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

## Load dev data from an eVital export

Stock exports are internal data: keep them **outside the repo** (or in `data/`, which is
git-ignored, as is `*.xlsx`). The script only writes to a local `instamed_dev` or
`instamed_test` database and refuses anything else.

```powershell
python -m scripts.seed_evital --file "C:\path\to\export.xlsx" --dry-run   # report only
python -m scripts.seed_evital --file "C:\path\to\export.xlsx"             # load
```

`--reset` drops the app collections in the target dev db first. Re-running without it
updates existing rows and inserts nothing twice.

It reads the sheet whose name starts with `FINAL` and keeps only rows with full details:
salt, HSN, known schedule, valid GST and MRP, at least one full pack, and at least 30 days
to expiry (MM/YY means the end of that month). Duplicate (name, pack) rows are dropped
entirely. The purchase price (PTR) column is never read. Everything is stocked in one dev
store ("InstaMed Indirapuram (dev)") that serves pincode `201014`, priced at MRP.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `instamed` | Database name |
| `LOG_LEVEL` | `INFO` | Log level for the `instamed` loggers |

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
| GET | `/` | Welcome message |
| GET | `/health` | 200 `{"status": "ok"}` when Mongo answers, 503 otherwise |
| GET | `/test-db` | List collections (dev only, removed in Phase 3) |
| GET | `/search?pincode=&medicine_name=` | Price and stock of a medicine for a pincode (name is case-insensitive) |

Rules worth knowing:
- A medicine is a catalog item: one product in one pack size, unique by (name, pack_size).
  It carries `mrp`, `schedule` (H/H1/X need a prescription; G/OTC do not), `gst_percent`
  and `hsn_code`.
- Inventory is the stock of one medicine at one store: `quantity` in packs, selling `price`,
  `earliest_expiry`, `batch_count`, shelf `location`.
- One inventory row per (store, medicine); one zone per pincode.
- Inventory `medicine_id`/`store_id` and zone `warehouse_id` must point at existing documents.
- Pincodes are 6-digit Indian PINs (first digit 1-9).

### Breaking changes in v0.3.0
- Medicine `price` is now `mrp`; new required fields `pack_size`, `gst_percent`, `hsn_code`.
- Medicine `expiry_date` is removed; use inventory `earliest_expiry`.
- Creating a second medicine with the same (name, pack_size) returns 409.

### Breaking changes in v0.2.0
- `PUT /medicines/{id}` is now `PATCH` (send only the fields to change).
- `POST /pincode_zone` and `GET /pincode-zone` are now `/pincode-zones`.
- Errors return proper HTTP status codes with `{"detail": "..."}` instead of `200 {"error": "..."}`.

## Roadmap

- [x] Phase 0: Foundation (config, tests, lint, docs)
- [x] Phase 1: Correctness (status codes, validation, pagination, full CRUD)
- [x] Phase 2: Layered architecture, logging, request ids, health check
- [ ] Phase 3: Authentication and roles (JWT)
- [ ] Phase 4: Orders, cart, prescriptions, atomic stock updates
- [ ] Phase 5: Elasticsearch medicine search
- [ ] Phase 6: Docker, CI, pre-commit

## Observability

Every response carries an `X-Request-ID` header (the caller's, or a generated one). Each
request writes one access log line, `METHOD /path STATUS 12.3ms`, tagged with that id. Any
unhandled error is logged with its traceback, and the client receives
`500 {"detail": "Internal server error", "request_id": "..."}`, which is enough to find the
matching log line without leaking internals.

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
├── db.py            # Mongo client and database handle
├── core/config.py   # Settings loaded from env / .env
├── models/          # Pydantic request models
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

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `instamed` | Database name |

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health message |
| GET | `/test-db` | List collections (dev only, will be removed) |
| POST, GET | `/medicines` | Create / list medicines |
| GET, PUT, DELETE | `/medicines/{medicine_id}` | Read / update / delete one medicine |
| POST, GET | `/stores` | Create / list stores |
| POST, GET | `/inventory` | Create / list inventory items |
| POST | `/pincode_zone` | Map a pincode to a warehouse |
| GET | `/pincode-zone` | List pincode zones |
| GET | `/search?pincode=&medicine_name=` | Price and stock of a medicine for a pincode |

## Roadmap

- [x] Phase 0: Foundation (config, tests, lint, docs)
- [ ] Phase 1: Correctness (status codes, validation, pagination, full CRUD)
- [ ] Phase 2: Layered architecture, logging, indexes
- [ ] Phase 3: Authentication and roles (JWT)
- [ ] Phase 4: Orders, cart, prescriptions, atomic stock updates
- [ ] Phase 5: Elasticsearch medicine search
- [ ] Phase 6: Docker, CI, pre-commit

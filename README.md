# Project: FastAPI file registry

This repository previously used a local SQLite file (`users.db`) for user/brand/country data. The codebase has been migrated to use PostgreSQL with connection pooling.

## What I changed
- Switched DB backend from SQLite to PostgreSQL in `main.py` using `psycopg2` and a `ThreadedConnectionPool`.
- Added a migration script `migrate_sqlite_to_postgres.py` to copy existing data from `users.db` into Postgres.
- Added `psycopg2-binary` to `requirements.txt`.

## Environment
Create a `.env` file in the project root or set these env vars in your shell:

```
DATABASE_URL=postgres://user:password@host:5432/dbname
SECRET_KEY=your_jwt_secret
ADMIN_SECRET_KEY=your_admin_jwt_secret
# optional pool size
DB_MIN_CONN=1
DB_MAX_CONN=10
```

DATABASE_URL example for local Postgres:
```
postgres://postgres:mysecret@localhost:5432/mydb
```

## Migrate existing SQLite data
If you have an existing `users.db` in the project root, run:

```powershell
python migrate_sqlite_to_postgres.py
```

This will create the same tables in Postgres (if missing) and copy rows from `users`, `admin`, `brand`, and `country`. Duplicate unique keys are skipped.

## Run the app
Install dependencies and run Uvicorn:

```powershell
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Notes & Next steps
- For production, consider using a more robust pool configuration or switching to an async driver (e.g., `asyncpg` + `databases` or SQLAlchemy async).
- If you'd like, I can convert the app to async endpoints and use `databases` or SQLAlchemy async for better concurrency.
- Run the migration script before starting the app if you want to preserve existing data.

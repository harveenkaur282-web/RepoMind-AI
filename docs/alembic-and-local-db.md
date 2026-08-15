# Alembic and local database setup

This project stores ingested GitHub repository data in PostgreSQL, and Alembic is what keeps that database schema versioned and reproducible.

## Why we added Alembic

Without a migration tool, the database schema can drift over time:

- one developer creates a table manually in local Postgres
- another developer does not have the same table
- production and local environments end up with different schema
- future code changes become hard to reason about

That is exactly the problem Alembic solves. It gives us a proper, repeatable way to manage database changes.

In this project, the database is used to persist:

- repository metadata
- document content for each ingested file
- repository status such as `pending`, `ingesting`, `ready`, and `failed`

That lets us query the database later from the terminal, a GUI, or another service instead of keeping everything only in memory.

## What is already set up

The repo already contains:

- the Alembic config file: `alembic.ini`
- the migration environment: `alembic/env.py`
- the initial migration: `alembic/versions/b21b895ba1d5_create_repository_and_document_tables.py`

That initial migration creates the `repositories` and `documents` tables used by the ingestion flow.

## How Alembic works in this project

Alembic compares your SQLAlchemy models to the database and stores schema changes as migration files.

The flow is usually:

1. change a SQLAlchemy model
2. generate a migration
3. review the migration file
4. run `alembic upgrade head`
5. your database schema matches the app code

This is important because we want the database schema to be treated like code: tracked, reviewed, and applied in a predictable way.

## Local database setup

The project uses PostgreSQL through Docker Compose.

### Start Postgres

From the project root:

```bash
docker compose up -d postgres
```

This starts the local database with these settings:

- username: `repomind`
- password: `repomind`
- database: `repomind`
- port: `5432`

The values also match the default app config in `backend/app/core/config.py`.

## Run the Alembic migration

Once Postgres is up, apply the schema:

```bash
uv run alembic upgrade head
```

This runs all pending migration files in order and creates the tables needed by the app.

If you are creating a new migration later, do this:

```bash
uv run alembic revision --autogenerate -m "your migration name"
```

Then apply it:

```bash
uv run alembic upgrade head
```

## Checking the database

After starting Postgres and running migrations, you can inspect the schema and data.

### List tables

```bash
docker compose exec postgres psql -U repomind -d repomind -c "\dt"
```

### View repository rows

```bash
docker compose exec postgres psql -U repomind -d repomind -c "SELECT * FROM repositories;"
```

### View document rows

```bash
docker compose exec postgres psql -U repomind -d repomind -c "SELECT * FROM documents ORDER BY created_at;"
```

### Check repository + document counts

```bash
docker compose exec postgres psql -U repomind -d repomind -c "SELECT r.owner, r.name, COUNT(d.id) AS document_count FROM repositories r LEFT JOIN documents d ON d.repository_id = r.id GROUP BY r.owner, r.name ORDER BY r.owner, r.name;"
```

## Why this matters for RepoMind

This project is meant to ingest many repositories and later answer questions like:

- which repositories are stored?
- which files were ingested?
- what repo does this file belong to?
- what is the status of ingestion?

Without a real database and a migration system, none of that would be stable or queryable. Alembic gives us a safe way to evolve that schema as the app grows.

In short: Alembic is the layer that makes the database predictable, shareable, and version-controlled.

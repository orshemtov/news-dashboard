---
name: db-migrate
description: Create and run Alembic database migrations for the news-dashboard PostgreSQL database with pgvector support
---

## Overview

This project uses Alembic for database migrations with async SQLAlchemy and the pgvector extension.

## Running migrations

```bash
# Apply all pending migrations
cd backend && uv run alembic upgrade head

# Or via mise
cd backend && mise run migrate
```

## Creating a new migration

```bash
# Auto-generate from model changes
cd backend && uv run alembic revision --autogenerate -m "describe the change"

# Or via mise
cd backend && mise run migrate-new -- "describe the change"
```

## Key files

| File | Purpose |
|------|---------|
| `backend/alembic.ini` | Alembic config, points to `alembic/` directory |
| `backend/alembic/env.py` | Migration environment, imports all models for autogenerate |
| `backend/alembic/versions/` | Generated migration scripts |
| `backend/src/app/models/base.py` | `DeclarativeBase` + `TimestampMixin` |
| `backend/src/app/models/article.py` | Article model with pgvector `Vector(384)` column |
| `backend/src/app/models/source.py` | Source model with RSS/Telegram config |

## Important: model imports in env.py

For autogenerate to detect changes, `alembic/env.py` must import all models. Verify this line exists:

```python
from app.models.base import Base
from app.models.article import Article
from app.models.source import Source

target_metadata = Base.metadata
```

If you add a new model file, you **must** add its import to `env.py` or autogenerate will not detect it.

## pgvector specifics

The `articles` table uses a `Vector(384)` column for embeddings. When creating the initial migration, ensure the migration includes:

```python
from pgvector.sqlalchemy import Vector

# In the upgrade function, the column should be:
sa.Column('embedding', Vector(384), nullable=True)
```

The pgvector extension must be enabled in the database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Add this to the first migration's `upgrade()` function:

```python
op.execute('CREATE EXTENSION IF NOT EXISTS vector')
```

## Common migration patterns

### Adding a column

```python
def upgrade():
    op.add_column('articles', sa.Column('sentiment', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('articles', 'sentiment')
```

### Adding an index

```python
def upgrade():
    op.create_index('ix_articles_source_id', 'articles', ['source_id'])

def downgrade():
    op.drop_index('ix_articles_source_id')
```

### Adding a new table

Create the model in `backend/src/app/models/`, import it in `env.py`, then run autogenerate.

## Troubleshooting

- **"Target database is not up to date"**: Run `uv run alembic upgrade head` first
- **Empty migration generated**: Check that the new model is imported in `env.py`
- **pgvector errors**: Ensure the `vector` extension is installed in PostgreSQL (`pgvector/pgvector:pg16` Docker image includes it)
- **Connection refused**: Ensure PostgreSQL is running (`mise run infra` or `docker compose up -d postgres`)

---
description: Create or run Alembic database migrations
---

Handle database migrations for the project. Use the `db-migrate` skill for detailed patterns.

If $ARGUMENTS contains a migration message, create a new migration:
!`cd backend && uv run alembic revision --autogenerate -m "$ARGUMENTS"`

If no arguments are provided, apply all pending migrations:
!`cd backend && uv run alembic upgrade head`

After running, show the current migration status:
!`cd backend && uv run alembic current`

Report what happened and flag any issues (empty migrations, failed upgrades, missing model imports in env.py).

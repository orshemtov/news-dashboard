# Pulse

A real-time news aggregator dashboard. Collects articles from Telegram channels, deduplicates them using semantic similarity, and provides hybrid search.

## Project Structure

```
news-dashboard/
├── backend/            # Python 3.13, FastAPI, SQLAlchemy (async), Alembic
│   └── src/app/
│       ├── api/        # REST API routes (articles, sources, search, stats, media)
│       ├── models/     # SQLAlchemy ORM models (article, source)
│       ├── schemas/    # Pydantic request/response schemas
│       ├── services/   # Business logic (search, embedding, dedup, ingestion, events, telegram_listener)
│       ├── ingestors/  # Data source adapters (telegram)
│       └── db/         # Async database session factory
├── frontend/           # React 19, TypeScript, Vite 7, Tailwind CSS 4, shadcn/ui
│   └── src/
│       ├── api/        # Axios API client
│       ├── hooks/      # React Query hooks + SSE article stream
│       ├── pages/      # Route pages (Feed, Sources)
│       ├── components/ # UI components organized by feature
│       └── types/      # TypeScript interfaces
├── docker-compose.yml  # PostgreSQL 16 (pgvector)
├── mise.toml           # Root task runner config (infra, dev, setup)
└── .opencode/          # OpenCode config, agents, skills, commands
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Alembic |
| Frontend | React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4, shadcn/ui |
| Database | PostgreSQL 16 with pgvector extension (384-dim embeddings) |
| Embeddings | sentence-transformers (default: paraphrase-multilingual-MiniLM-L12-v2) |
| Package Managers | uv (backend), pnpm (frontend) |
| Task Runner | mise (replaces Make) |

## API Routes

All routes are prefixed with `/api`:

| Prefix | Purpose |
|--------|---------|
| `/api/articles` | List, get, delete articles with filtering/pagination |
| `/api/sources` | CRUD for news sources (RSS/Telegram), test connection, presets |
| `/api/search` | Keyword, semantic, and hybrid (RRF) search |
| `/api/stats` | Dashboard statistics |
| `/api/media` | Proxy for Telegram media (images, videos) |
| `/api/health` | Health check |

## Database Models

- `articles` -- news articles with pgvector embeddings (Vector(384)), dedup_hash, JSONB metadata, GIN indexes
- `sources` -- RSS/Telegram source configurations with polling metadata

## Coding Standards

### Python (backend)

- Use `async def` for all route handlers and service methods
- Use SQLAlchemy async session patterns (`async with session.begin()`)
- Use Pydantic models for all request/response validation
- Use `pydantic-settings` for configuration (all settings in `config.py`)
- Type annotations on all function signatures
- Use `loguru` for logging (not stdlib `logging`)
- Use `ruff` for linting and formatting
- Use `ty` for type checking
- Tests with `pytest` + `pytest-asyncio`, run via `uv run pytest`

### TypeScript (frontend)

- Use functional components with hooks
- Use `@tanstack/react-query` for all server state
- Use shadcn/ui primitives -- do not reinvent UI components
- Use `cn()` utility from `src/lib/utils.ts` for conditional class merging
- Use path alias `@/` for imports (maps to `src/`)
- Follow shadcn/ui New York style with neutral base color

### General

- Environment variables defined in `.env` (copy from `.env.example`)
- Infrastructure managed via Docker Compose
- Backend and frontend run locally outside Docker
- Prefer `mise run` commands for common tasks

## Development Commands

```bash
# Root (from project root)
mise run setup          # First-time setup (copies .env, installs deps, starts infra, runs migrations)
mise run dev            # Start everything (infra + backend + frontend)
mise run infra          # Start Docker services
mise run infra-down     # Stop Docker services
mise run infra-reset    # Reset all Docker volumes

# Backend (from backend/)
mise run serve          # FastAPI dev server on port 8000
mise run migrate        # Apply Alembic migrations
mise run migrate-new -- "description"  # Create new migration
mise run lint           # Lint backend code
mise run format         # Format backend code
mise run typecheck      # Run ty type checker
mise run test           # Run backend tests
mise run check          # Run all checks (lint + typecheck + test)

# Frontend (from frontend/)
mise run serve          # Vite dev server on port 5173
mise run build          # Build frontend for production
mise run lint           # Lint frontend code
```

## Key Patterns

- **Dedup**: Two-tier deduplication -- exact hash matching + semantic similarity (0.92 cosine threshold, 24h window)
- **Search**: Hybrid search using Reciprocal Rank Fusion (RRF) combining keyword (GIN/tsvector) and semantic (pgvector cosine) search
- **Ingestion Pipeline**: Telegram listener (real-time) + polling (fallback) -> embed + dedup -> PostgreSQL, SSE push to frontend

## When using MCP tools

- Use `playwright` to navigate and screenshot the frontend at http://localhost:5173
- Use `postgres` to inspect database schemas and query data (read-only)
- Use `context7` to look up documentation for any library in the stack

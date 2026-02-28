# Pulse

A real-time news aggregator that collects articles from Telegram channels, deduplicates them using semantic similarity, and provides hybrid search (keyword + vector). Built for speed -- articles appear in your feed within seconds of being posted.

![Feed - Dark](docs/feed-dark.png)

<details>
<summary>Light mode</summary>

![Feed - Light](docs/feed-light.png)

</details>

## Features

### Real-Time Feed

Articles stream in via Server-Sent Events (SSE) -- no manual refresh needed. Each article shows source name, relative timestamp, and a direct link to the original Telegram post. Rich media (images, videos with duration badges) renders inline.

![Feed with media](docs/feed-scroll2-dark.png)

- **Time range filtering** -- quick presets from 1 minute to 30 days
- **Sort & dedup** -- newest/oldest, hide semantic duplicates
- **Pagination** -- 20 articles per page
- **RTL support** -- automatic right-to-left layout for Hebrew, Arabic, Farsi, Urdu
- **Stats bar** -- total articles, today's count, active sources, last update time
- **Article detail** -- click any article to see full content with source link

![Article detail](docs/article-detail.png)

### Search

Three search modes integrated directly into the feed:

![Search](docs/search-dark.png)

- **Keyword** -- PostgreSQL full-text search with `ts_rank` scoring
- **Semantic** -- pgvector cosine similarity against query embeddings
- **Hybrid** (default) -- combines both using Reciprocal Rank Fusion (RRF)

### Source Management

Add Telegram channels by searching directly from the app. Channels show active/disabled status, article count, and last poll time. Articles begin ingesting immediately when a source is added.

![Sources](docs/sources-dark.png)

Search for any public Telegram channel and add it with one click:

![Channel search](docs/channel-search.png)

### Other

- **Dark/light mode** toggle
- **Responsive layout** with sticky header
- **Telegram content cleaning** -- strips formatting artifacts
- **Media proxy** -- serves Telegram images and videos through the backend

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Alembic |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4, shadcn/ui |
| Database | PostgreSQL 16 with pgvector (384-dim embeddings) |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| Task Runner | [mise](https://mise.jdx.dev/) |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [mise](https://mise.jdx.dev/) (task runner)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node package manager)
- Python 3.13+
- Node.js 22+

## Setup

```bash
git clone https://github.com/<your-username>/news-dashboard.git
cd news-dashboard

# First-time setup (copies .env, installs deps, starts infra, runs migrations)
mise run setup
```

This will:
1. Copy `.env.example` to `.env`
2. Install backend (uv) and frontend (pnpm) dependencies
3. Start Docker services (PostgreSQL, Ollama)
4. Run database migrations

### Telegram credentials

To ingest from Telegram channels, you need API credentials from [my.telegram.org](https://my.telegram.org):

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

## Usage

### Start everything

```bash
mise run dev
```

This starts infrastructure (Docker), runs migrations, and launches:
- **Backend API** at http://localhost:8000
- **Frontend** at http://localhost:5173

### Start components individually

```bash
# Infrastructure only (Postgres, Ollama)
mise run infra

# Backend API server (from backend/)
mise run serve

# Frontend dev server (from frontend/)
mise run serve
```

### Adding news sources

1. Open http://localhost:5173
2. Go to **Sources**
3. Search for a Telegram channel and click **Add**
4. Articles begin ingesting immediately

### Database migrations

```bash
# Apply migrations
cd backend && mise run migrate

# Create a new migration
cd backend && mise run migrate-new -- "description"
```

### Run checks

```bash
cd backend && mise run check   # lint + typecheck + test
cd frontend && mise run lint   # lint frontend
cd frontend && mise run build  # type-check + build
```

### Stop infrastructure

```bash
mise run infra-down     # Stop containers
mise run infra-reset    # Stop containers and delete all data
```

## Configuration

All configuration is through environment variables in `.env`. The defaults in `.env.example` work out of the box for local development.

### All Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/news_dashboard` | PostgreSQL connection string |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Embedding model (sentence-transformers) |
| `EMBEDDING_DIMENSIONS` | `384` | Embedding vector dimensions |
| `DEDUP_SIMILARITY_THRESHOLD` | `0.92` | Cosine similarity threshold for dedup |
| `DEDUP_WINDOW_HOURS` | `24` | Time window for dedup comparison |
| `TELEGRAM_API_ID` | | Telegram API ID |
| `TELEGRAM_API_HASH` | | Telegram API hash |
| `TELEGRAM_SESSION_NAME` | `news_dashboard` | Telethon session file name |
| `TELEGRAM_POLL_INTERVAL_SECONDS` | `60` | Telegram polling interval |
| `INITIAL_BACKFILL_HOURS` | `24` | Hours of history to backfill on first run |
| `POLLING_ENABLED` | `true` | Enable/disable source polling |
| `POLLING_INTERVAL_SECONDS` | `300` | Source polling interval |

## Architecture

```
Telegram Channels
      │
      ├──────────────────────────┐
      ▼                          ▼
  Real-time Listener       Polling (fallback)
  (Telethon events)        (per-source interval)
      │                          │
      └──────────┬───────────────┘
                 │
           embed + dedup
                 │
                 ▼
            PostgreSQL
            (pgvector)
                 │
          ┌──────┴──────┐
          ▼              ▼
    FastAPI API      SSE Stream
          │              │
          ▼              ▼
       React Frontend
```

### Ingestion Pipeline

Two complementary ingestion paths run simultaneously:

**Real-time listener** -- A Telethon event handler listens for `NewMessage` events from all configured Telegram channels. New messages are processed immediately through the embed + dedup pipeline and stored to PostgreSQL. An SSE event is pushed to all connected frontend clients for instant UI updates.

**Polling (fallback)** -- A background task checks all enabled sources on a 60-second loop. Each source has its own `poll_interval_seconds` setting. Uses cursor-based fetching (`min_id`) to only retrieve messages newer than the last ingested one. Catches any messages missed by the real-time listener.

### Deduplication

Two-tier system to catch both exact and near-duplicate articles:

1. **Exact hash** -- SHA-256 of normalized content. Exact duplicates are silently skipped.
2. **Semantic similarity** -- pgvector cosine distance against articles within a configurable time window (default 24h). Articles above the threshold (default 0.92) are stored but marked as `is_duplicate=true`.

### Hybrid Search (RRF)

Search runs keyword and semantic queries in parallel, then merges results using Reciprocal Rank Fusion:

- **Keyword** -- PostgreSQL full-text search with `plainto_tsquery("simple", ...)` and `ts_rank` scoring. The `simple` config handles multilingual content (Hebrew, Arabic, English).
- **Semantic** -- generates a query embedding, finds nearest neighbors via pgvector cosine distance.
- **Fusion** -- `RRF_score = sum(1 / (k + rank))` across both result lists (k=60). Articles appearing in both lists get boosted scores.

## Project Structure

```
news-dashboard/
├── backend/
│   └── src/app/
│       ├── api/          # REST API routes (articles, sources, search, stats, media)
│       ├── models/       # SQLAlchemy ORM models (article, source)
│       ├── schemas/      # Pydantic request/response schemas
│       ├── services/     # Business logic (search, embedding, dedup, ingestion, events)
│       ├── ingestors/    # Data source adapters (Telegram)
│       └── db/           # Async database session factory
├── frontend/
│   └── src/
│       ├── api/          # Axios API client
│       ├── hooks/        # React Query hooks + SSE article stream
│       ├── pages/        # Route pages (Feed, Sources)
│       ├── components/   # UI components organized by feature
│       └── types/        # TypeScript interfaces
├── docker-compose.yml    # PostgreSQL, Ollama
└── mise.toml             # Task runner configuration
```

## License

This project is not currently licensed. All rights reserved.

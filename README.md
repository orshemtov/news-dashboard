# News Dashboard

A full-stack news aggregator dashboard with AI-powered search and chat. Collects articles from Telegram channels, deduplicates them using semantic similarity, and provides hybrid search (keyword + vector) with a RAG-based conversational interface.

| Light | Dark |
|-------|------|
| ![Feed - Light](docs/feed-light.png) | ![Feed - Dark](docs/feed-dark.png) |

## Features

### Article Feed

Articles displayed as cards with title, preview, source badge, timestamp, and language tag. Click to open full content with source link.

- **Time range filtering** -- quick presets from 1 minute to all time
- **Auto-refresh** -- configurable interval, default 10s
- **Sort, dedup, pagination** -- newest/oldest, hide duplicates, 20 per page
- **RTL support** -- automatic right-to-left layout for Hebrew, Arabic, Farsi, Urdu
- **Stats bar** -- article counts, active sources, last ingestion time

### Search

Integrated into the feed with three modes:

- **Keyword** -- PostgreSQL full-text search
- **Semantic** -- pgvector cosine similarity
- **Hybrid** -- combines both using Reciprocal Rank Fusion (RRF)

### Source Management

Add, enable/disable, and delete Telegram channels. Articles begin ingesting immediately when a source is added. Includes live channel search via Telegram API and built-in presets.

![Sources](docs/sources-dark.png)

### AI Chat (News Copilot)

Floating chat panel with RAG-based Q&A over your articles. Uses hybrid search to find relevant articles, sends them as context to the LLM, and returns answers with numbered `[1]`, `[2]` citations. Multi-turn conversations with persistence. Works with Ollama (local) or OpenAI.

### Other

- **Dark mode** toggle
- **Responsive layout** with sticky header
- **Telegram content cleaning** -- strips formatting artifacts

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Alembic |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4, shadcn/ui |
| Database | PostgreSQL 16 with pgvector (384-dim embeddings) |
| AI/LLM | Ollama (llama3.1:8b) or OpenAI (gpt-4o-mini) |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) or OpenAI |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [mise](https://mise.jdx.dev/) (task runner)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node package manager)
- Python 3.13+
- Node.js 22+

## Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/news-dashboard.git
cd news-dashboard

# Run first-time setup (copies .env, installs deps, starts infra, runs migrations)
mise run setup
```

This will:
1. Copy `.env.example` to `.env`
2. Install backend (uv) and frontend (pnpm) dependencies
3. Start Docker services (PostgreSQL, Ollama, pgweb)
4. Run database migrations

### Download the AI model

```bash
mise run ollama-pull
```

This pulls the default Ollama model (`llama3.1:8b`). To use a different model, set `MODEL`:

```bash
MODEL=mistral mise run ollama-pull
```

## Configuration

All configuration is done through environment variables in `.env`. The defaults in `.env.example` work out of the box for local development.

### LLM Provider

By default, the project uses Ollama running locally. To use OpenAI instead:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Embedding Provider

By default, embeddings are computed locally using sentence-transformers. To use OpenAI:

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Telegram Sources

To ingest from Telegram channels, you need API credentials from [my.telegram.org](https://my.telegram.org):

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### All Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/news_dashboard` | PostgreSQL connection string |
| `LLM_PROVIDER` | `ollama` | LLM provider (`ollama` or `openai`) |
| `LLM_MODEL` | `llama3.1:8b` | Model name for the configured provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | | OpenAI API key (required if using OpenAI provider) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `EMBEDDING_PROVIDER` | `local` | Embedding provider (`local` or `openai`) |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Local embedding model |
| `EMBEDDING_DIMENSIONS` | `384` | Embedding vector dimensions |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `DEDUP_SIMILARITY_THRESHOLD` | `0.92` | Cosine similarity threshold for dedup |
| `DEDUP_WINDOW_HOURS` | `24` | Time window for dedup comparison |
| `TELEGRAM_API_ID` | | Telegram API ID |
| `TELEGRAM_API_HASH` | | Telegram API hash |
| `TELEGRAM_SESSION_NAME` | `news_dashboard` | Telethon session file name |
| `TELEGRAM_POLL_INTERVAL_SECONDS` | `60` | Telegram polling interval |
| `INITIAL_BACKFILL_HOURS` | `24` | Hours of history to backfill on first run |
| `POLLING_ENABLED` | `true` | Enable/disable source polling |
| `POLLING_INTERVAL_SECONDS` | `300` | Source polling interval |

## Usage

### Start everything

```bash
mise run dev
```

This starts the infrastructure (Docker), runs migrations, and launches:
- **Backend API** at http://localhost:8000
- **Frontend** at http://localhost:5173
- **pgweb** (database UI) at http://localhost:8081

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

1. Open the frontend at http://localhost:5173
2. Navigate to **Sources**
3. Add a Telegram channel
4. Articles will begin ingesting automatically

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

## Project Structure

```
news-dashboard/
├── backend/
│   └── src/app/
│       ├── api/          # REST API routes
│       ├── models/       # SQLAlchemy ORM models
│       ├── schemas/      # Pydantic request/response schemas
│       ├── services/     # Business logic (AI, search, embedding, dedup, ingestion, events, telegram_listener)
│       ├── ingestors/    # Data source adapters (Telegram)
│       └── db/           # Async database session factory
├── frontend/
│   └── src/
│       ├── api/          # Axios API client
│       ├── hooks/        # React Query hooks + SSE article stream
│       ├── pages/        # Route pages (Feed, Search, Sources, Stats, Chat)
│       ├── components/   # UI components organized by feature
│       └── types/        # TypeScript interfaces
├── docker-compose.yml    # PostgreSQL, Ollama, pgweb
└── mise.toml             # Task runner configuration
```

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

**Real-time listener (primary)** -- A Telethon event handler listens for `NewMessage` events from all configured Telegram channels. New messages are processed immediately through the embed + dedup pipeline and stored to PostgreSQL. An SSE event is pushed to all connected frontend clients, triggering an instant UI refresh.

**Polling (fallback/catch-up)** -- A background task checks all enabled sources on a 60-second loop. Each source has its own `poll_interval_seconds` setting, and only sources due for a poll are processed. Uses cursor-based fetching (`min_id`) to only retrieve messages newer than the last ingested one. This catches any messages missed by the real-time listener.

### Deduplication

Two-tier system to catch both exact and near-duplicate articles:

1. **Exact hash** -- SHA-256 of normalized (lowercased, trimmed) content. Checked before insertion; exact duplicates are silently skipped.
2. **Semantic similarity** -- pgvector cosine distance against articles within a configurable time window (default: 24h). Articles above the similarity threshold (default: 0.92) are stored but marked as `is_duplicate=true` and assigned to a `dedup_cluster_id`.

### Hybrid Search (RRF)

Search runs keyword and semantic queries in parallel, then merges results using Reciprocal Rank Fusion:

- **Keyword** -- PostgreSQL full-text search with `plainto_tsquery("simple", ...)` and `ts_rank` scoring. The `simple` config handles multilingual content (Hebrew, Arabic, English).
- **Semantic** -- generates a query embedding, finds nearest neighbors via pgvector cosine distance (`<=>`).
- **Fusion** -- `RRF_score = sum(1 / (k + rank))` across both result lists (k=60). Articles appearing in both lists get boosted scores. Pagination is applied after fusion.

### RAG Chat

1. User message is used as a hybrid search query (top 10 articles, duplicates excluded)
2. Articles are formatted as numbered context blocks (first 1500 chars each)
3. Context + question are sent to the LLM with a system prompt enforcing citation-based answers
4. Response is parsed for `[N]` citation markers and mapped back to article IDs
5. Conversations and messages are persisted to the database

Uses pydantic-ai for LLM orchestration. Supports Ollama (local) or OpenAI.

## License

This project is not currently licensed. All rights reserved.

# News Dashboard

A full-stack news aggregator dashboard with AI-powered search, summarization, and chat. Collects articles from RSS feeds and Telegram channels, deduplicates them using semantic similarity, and provides hybrid search (keyword + vector) with a RAG-based conversational interface.

| Light | Dark |
|-------|------|
| ![Feed - Light](docs/feed-light.png) | ![Feed - Dark](docs/feed-dark.png) |

## Features

### Article Feed

The main page displays articles as cards with title, content preview, source badge, relative timestamp, and language tag. Clicking a card opens a detail dialog with the full content, source link, and summary (if available).

- **Time range filtering** -- Datadog-style presets (1m, 5m, 15m, 1h, 4h, 12h, 1d, 3d, 7d, 30d, All)
- **Auto-refresh** -- configurable intervals (5s, 10s, 30s, 1m, 5m, Off), default 10s
- **Sort order** -- toggle between newest and oldest first
- **Hide duplicates** -- filter out semantically duplicate articles
- **Pagination** -- 20 articles per page with total count
- **RTL support** -- automatic right-to-left layout for Hebrew, Arabic, Farsi, and Urdu content
- **Stats bar** -- total articles, articles today, active sources, last ingestion time

### Search

Search is integrated directly into the feed with three modes:

- **Keyword** -- PostgreSQL full-text search with `plainto_tsquery` and `ts_rank` ranking
- **Semantic** -- vector similarity search using pgvector cosine distance
- **Hybrid** -- runs both keyword and semantic, merges results with Reciprocal Rank Fusion (RRF, k=60)

All modes support filtering by source, source type, language, and date range.

### Source Management

Add, enable/disable, and delete news sources. Articles begin ingesting immediately when a source is added.

- **Telegram channel search** -- live search via Telegram API, with fallback to built-in presets
- **Preset sources** -- curated list of news channels available out of the box
- **Status tracking** -- active/disabled/error states with error message display
- **Article counts** and last-polled timestamps per source

![Sources](docs/sources-dark.png)

### AI Chat (News Copilot)

A floating chat panel in the bottom-right corner provides RAG-based conversational Q&A:

1. Your message is used as a hybrid search query to retrieve the top 10 relevant articles
2. Articles are formatted as numbered context and sent to the LLM
3. The model answers based only on retrieved articles, citing sources with `[1]`, `[2]` notation
4. Citations are displayed as clickable badges below the response

Supports multi-turn conversations with persistence. Works with Ollama (local) or OpenAI.

### AI Summarization and Translation

Backend services for article summarization (2-4 sentence summaries) and translation to any target language, powered by the configured LLM provider.

### Other

- **Dark mode** -- toggle via header button
- **Responsive layout** -- mobile-friendly with sticky header and backdrop blur
- **Telegram content cleaning** -- strips markdown formatting, bare URLs, and navigation elements

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy (async) + asyncpg, Alembic |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4, shadcn/ui |
| Database | PostgreSQL 16 with pgvector (384-dim embeddings) |
| Messaging | Apache Kafka (KRaft mode) |
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
3. Start Docker services (PostgreSQL, Kafka, Ollama, pgweb)
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
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
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
| `POLLING_INTERVAL_SECONDS` | `300` | RSS polling interval |

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
# Infrastructure only (Postgres, Kafka, Ollama)
mise run infra

# Backend API server (from backend/)
mise run serve

# Kafka consumer worker (from backend/)
mise run worker

# Frontend dev server (from frontend/)
mise run serve
```

### Adding news sources

1. Open the frontend at http://localhost:5173
2. Navigate to **Sources**
3. Add an RSS feed URL or Telegram channel
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
│       ├── services/     # Business logic (AI, search, embedding, dedup, ingestion)
│       ├── ingestors/    # Data source adapters (RSS, Telegram)
│       ├── workers/      # Kafka consumer worker
│       └── db/           # Async database session factory
├── frontend/
│   └── src/
│       ├── api/          # Axios API client
│       ├── hooks/        # React Query hooks
│       ├── pages/        # Route pages (Feed, Search, Sources, Stats, Chat)
│       ├── components/   # UI components organized by feature
│       └── types/        # TypeScript interfaces
├── docker-compose.yml    # PostgreSQL, Kafka, Ollama, pgweb
└── mise.toml             # Task runner configuration
```

## Architecture

```
RSS / Telegram
      │
      ▼
  Ingestors ──▶ Kafka (raw-articles) ──▶ Consumer Worker
                                              │
                                        embed + dedup
                                              │
                                              ▼
                                    Kafka (enriched-articles)
                                              │
                                              ▼
                                         PostgreSQL
                                         (pgvector)
                                              │
                                              ▼
                                     FastAPI Backend
                                              │
                                              ▼
                                    React Frontend
```

## License

This project is not currently licensed. All rights reserved.

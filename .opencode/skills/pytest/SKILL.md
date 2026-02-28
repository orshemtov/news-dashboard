---
name: pytest
description: Write and run tests for the news-dashboard Python backend using pytest with async support, fixtures, and proper mocking patterns
---

## Testing setup

This project uses `pytest` with `pytest-asyncio` for async test support. All tests run via:

```bash
cd backend && uv run pytest
```

Or with coverage:

```bash
cd backend && uv run pytest --cov=src/app --cov-report=term-missing
```

## Project test structure

Place tests in `backend/tests/` mirroring the source layout:

```
backend/tests/
├── conftest.py              # Shared fixtures (db session, test client, factories)
├── api/
│   ├── test_articles.py
│   ├── test_sources.py
│   ├── test_search.py
│   ├── test_stats.py
│   ├── test_ai.py
│   └── test_chat.py
├── services/
│   ├── test_ai.py
│   ├── test_chat.py
│   ├── test_search.py
│   ├── test_embedding.py
│   ├── test_dedup.py
│   └── test_ingestion.py
├── ingestors/
│   ├── test_rss.py
│   └── test_telegram.py
```

## Key patterns

### Async test functions

All tests must use `pytest.mark.asyncio` and `async def`:

```python
import pytest

@pytest.mark.asyncio
async def test_create_article(async_client, db_session):
    response = await async_client.post("/api/articles", json={...})
    assert response.status_code == 201
```

### Test client fixture

Use `httpx.AsyncClient` with the FastAPI app for API tests:

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import create_app

@pytest.fixture
async def async_client():
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
```

### Database fixture

Use a test database with transaction rollback per test:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/news_dashboard_test")
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()
```

### Mocking external services

Mock the embedding service and LLM calls:

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.embedding.EmbeddingService") as mock:
        instance = mock.return_value
        instance.embed_text = AsyncMock(return_value=[0.1] * 384)
        yield instance
```

### Factory fixtures for models

```python
from app.models.article import Article
from app.models.source import Source

@pytest.fixture
def article_factory(db_session):
    async def _create(**kwargs):
        defaults = {
            "title": "Test Article",
            "content": "Test content",
            "url": "https://example.com/test",
            "source_id": 1,
        }
        defaults.update(kwargs)
        article = Article(**defaults)
        db_session.add(article)
        await db_session.flush()
        return article
    return _create
```

## What to test

- **API endpoints**: Status codes, response schemas, filtering, pagination, error cases
- **Services**: Business logic (search ranking, dedup thresholds, chat RAG pipeline)
- **Ingestors**: RSS parsing (use fixture XML), Telegram message transformation

## What NOT to mock

- SQLAlchemy queries (use a real test database)
- Pydantic schema validation (let it validate naturally)

## What to ALWAYS mock

- External HTTP calls (RSS feeds, Telegram API)
- LLM/embedding API calls (Ollama, OpenAI)
- `sentence-transformers` model loading (slow, large)

import asyncio
import contextlib
import importlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.db.session import async_session_factory
from app.services.ingestion import ingest_all_sources

# ---------------------------------------------------------------------------
# Router registry – each entry is (module_path, prefix, tag)
# Routers that haven't been created yet are skipped gracefully.
# ---------------------------------------------------------------------------
_ROUTERS: list[tuple[str, str, str]] = [
    ("app.api.articles", "/api/articles", "articles"),
    ("app.api.sources", "/api/sources", "sources"),
    ("app.api.search", "/api/search", "search"),
    ("app.api.stats", "/api/stats", "stats"),
    ("app.api.chat", "/api/chat", "chat"),
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("News Dashboard API starting up")

    settings = get_settings()
    polling_task: asyncio.Task | None = None

    # Connect shared Telegram client (if credentials are configured)
    if settings.telegram_api_id and settings.telegram_api_hash:
        from app.services.telegram_client import get_telegram_client

        try:
            client = await get_telegram_client()
            logger.info("Telegram client ready")

            # Start real-time listener for instant message delivery
            from app.services.telegram_listener import start_realtime_listener

            try:
                await start_realtime_listener(client)
            except Exception:
                logger.warning(
                    "Real-time Telegram listener failed to start — falling back to polling only"
                )
        except Exception:
            logger.warning("Telegram client failed to connect — ingestion will be unavailable")

    if settings.polling_enabled:
        polling_task = asyncio.create_task(_polling_loop(settings.polling_interval_seconds))
        logger.info(
            "Background polling enabled (interval={}s)",
            settings.polling_interval_seconds,
        )

    yield

    if polling_task is not None:
        polling_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await polling_task

    # Disconnect shared Telegram client
    from app.services.telegram_client import disconnect_telegram_client

    # Stop real-time listener before disconnecting
    if settings.telegram_api_id and settings.telegram_api_hash:
        from app.services.telegram_listener import stop_realtime_listener

        try:
            from app.services.telegram_client import get_telegram_client

            client = await get_telegram_client()
            await stop_realtime_listener(client)
        except Exception:
            pass

    await disconnect_telegram_client()

    logger.info("News Dashboard API shutting down")


async def _polling_loop(interval: int) -> None:
    """Periodically check for sources due for ingestion.

    The *interval* controls how often this loop wakes up and checks.
    Actual per-source polling frequency is governed by each source's
    ``poll_interval_seconds`` column, checked inside
    ``ingest_all_sources``.
    """
    # Wait a bit on startup before first poll to let things settle
    await asyncio.sleep(10)

    while True:
        try:
            async with async_session_factory() as db, db.begin():
                summary = await ingest_all_sources(db)
                if summary:
                    total = sum(summary.values())
                    logger.info(
                        "Polling cycle complete: {} new articles from {} sources",
                        total,
                        len(summary),
                    )
        except Exception:
            logger.exception("Error in polling cycle")

        await asyncio.sleep(interval)


def create_app() -> FastAPI:
    application = FastAPI(
        title="News Dashboard API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS – allow everything for local development
    application.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    for module_path, prefix, tag in _ROUTERS:
        try:
            module = importlib.import_module(module_path)
            router = getattr(module, "router", None)
            if router is not None:
                application.include_router(router, prefix=prefix, tags=[tag])
                logger.info("Registered router {} at {}", module_path, prefix)
            else:
                logger.warning("Module {} has no 'router' attribute – skipped", module_path)
        except ImportError:
            logger.warning("Router module {} not found – skipped", module_path)

    # Health check
    @application.get("/api/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()


def cli() -> None:
    """Entry point for the ``serve`` script."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

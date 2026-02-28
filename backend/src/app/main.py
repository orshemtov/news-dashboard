import importlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# ---------------------------------------------------------------------------
# Router registry – each entry is (module_path, prefix, tag)
# Routers that haven't been created yet are skipped gracefully.
# ---------------------------------------------------------------------------
_ROUTERS: list[tuple[str, str, str]] = [
    ("app.api.articles", "/api/articles", "articles"),
    ("app.api.sources", "/api/sources", "sources"),
    ("app.api.search", "/api/search", "search"),
    ("app.api.stats", "/api/stats", "stats"),
    ("app.api.ai", "/api/ai", "ai"),
    ("app.api.chat", "/api/chat", "chat"),
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("News Dashboard API starting up")
    yield
    logger.info("News Dashboard API shutting down")


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

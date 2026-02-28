from app.api.articles import router as articles_router
from app.api.media import router as media_router
from app.api.search import router as search_router
from app.api.sources import router as sources_router
from app.api.stats import router as stats_router

all_routers = [
    articles_router,
    sources_router,
    search_router,
    stats_router,
    media_router,
]

__all__ = [
    "all_routers",
    "articles_router",
    "media_router",
    "search_router",
    "sources_router",
    "stats_router",
]

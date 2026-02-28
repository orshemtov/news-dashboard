from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_articles: int
    articles_today: int
    active_sources: int
    total_sources: int
    articles_by_source: dict[str, int]  # source_name -> count
    articles_by_hour: list[dict]  # [{hour: str, count: int}]
    languages: dict[str, int]  # language -> count
    latest_ingestion: datetime | None = None

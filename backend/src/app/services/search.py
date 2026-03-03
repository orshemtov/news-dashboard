from collections import defaultdict
from uuid import UUID

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.search import SearchRequest
from app.services.embedding import EmbeddingService

# Reciprocal Rank Fusion constant (commonly 60)
RRF_K = 60


class SearchService:
    """Hybrid search combining full-text and vector similarity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._embedding_service = EmbeddingService()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(stmt: Select, request: SearchRequest) -> Select:
        """Apply common filters from a SearchRequest to a SELECT statement."""
        if request.sources:
            stmt = stmt.where(Article.source_name.in_(request.sources))
        if request.source_types:
            stmt = stmt.where(Article.source_type.in_(request.source_types))
        if request.language:
            stmt = stmt.where(Article.language == request.language)
        if request.from_date:
            stmt = stmt.where(Article.published_at >= request.from_date)
        if request.to_date:
            stmt = stmt.where(Article.published_at <= request.to_date)
        if not request.include_duplicates:
            stmt = stmt.where(Article.is_duplicate == False)  # noqa: E712

        # Facet-style filters
        if request.sources_include:
            stmt = stmt.where(Article.source_name.in_(request.sources_include))
        if request.sources_exclude:
            stmt = stmt.where(Article.source_name.notin_(request.sources_exclude))
        if request.languages_include:
            stmt = stmt.where(Article.language.in_(request.languages_include))
        if request.languages_exclude:
            stmt = stmt.where(Article.language.notin_(request.languages_exclude))
        if request.forwarded is not None:
            if request.forwarded:
                stmt = stmt.where(Article.metadata_["forwarded"].as_boolean().is_(True))
            else:
                stmt = stmt.where(Article.metadata_["forwarded"].as_boolean().isnot(True))
        if request.exclude_keywords:
            for kw in request.exclude_keywords:
                stmt = stmt.where(Article.content.not_ilike(f"%{kw}%"))

        return stmt

    # ------------------------------------------------------------------
    # Keyword search
    # ------------------------------------------------------------------

    async def keyword_search(
        self,
        query: str,
        *,
        limit: int = 50,
        request: SearchRequest | None = None,
    ) -> list[Article]:
        """Full-text search using PostgreSQL tsvector.

        Uses the 'simple' text-search config which works reasonably for
        both Hebrew and English content.
        """
        ts_query = func.plainto_tsquery("simple", query)
        ts_rank = func.ts_rank(
            func.to_tsvector("simple", Article.content),
            ts_query,
        )

        stmt = (
            select(Article)
            .where(func.to_tsvector("simple", Article.content).op("@@")(ts_query))
            .order_by(ts_rank.desc())
            .limit(limit)
        )

        if request is not None:
            stmt = self._apply_filters(stmt, request)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    async def semantic_search(
        self,
        query: str,
        *,
        limit: int = 50,
        request: SearchRequest | None = None,
    ) -> list[Article]:
        """Vector similarity search using pgvector cosine distance."""
        query_embedding = await self._embedding_service.embed(query)

        stmt = text(f"""
            SELECT id
            FROM articles
            WHERE embedding IS NOT NULL
            {self._build_raw_filters(request)}
            ORDER BY embedding <=> cast(:query_embedding AS vector)
            LIMIT :limit
        """)

        params: dict = {
            "query_embedding": str(query_embedding),
            "limit": limit,
        }
        params.update(self._build_raw_filter_params(request))

        result = await self.db.execute(stmt, params)
        ids = [row.id for row in result.all()]
        if not ids:
            return []

        # Reload full ORM objects while preserving order
        articles_stmt = select(Article).where(Article.id.in_(ids))
        articles_result = await self.db.execute(articles_stmt)
        articles_by_id: dict[UUID, Article] = {a.id: a for a in articles_result.scalars().all()}
        return [articles_by_id[aid] for aid in ids if aid in articles_by_id]

    # ------------------------------------------------------------------
    # Hybrid search (RRF)
    # ------------------------------------------------------------------

    async def hybrid_search(self, request: SearchRequest) -> tuple[list[Article], int]:
        """Combine keyword and semantic search with Reciprocal Rank Fusion.

        Returns a tuple of (articles, total_count).
        """
        # Hybrid: run both searches then merge via RRF
        # We always use hybrid search now, ignoring request.mode if it's set
        keyword_results, semantic_results = (
            await self.keyword_search(request.query, limit=request.page_size * 3, request=request),
            await self.semantic_search(
                request.query, limit=request.page_size * 3, request=request
            ),
        )

        fused = self._reciprocal_rank_fusion([keyword_results, semantic_results])
        total = len(fused)
        start = (request.page - 1) * request.page_size
        return fused[start : start + request.page_size], total

    # ------------------------------------------------------------------
    # RRF helper
    # ------------------------------------------------------------------

    @staticmethod
    def _reciprocal_rank_fusion(
        result_lists: list[list[Article]],
    ) -> list[Article]:
        """Merge multiple ranked lists using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank_i)) across all lists.
        """
        scores: dict[UUID, float] = defaultdict(float)
        article_map: dict[UUID, Article] = {}

        for results in result_lists:
            for rank, article in enumerate(results, start=1):
                scores[article.id] += 1.0 / (RRF_K + rank)
                article_map[article.id] = article

        sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)
        return [article_map[aid] for aid in sorted_ids]

    # ------------------------------------------------------------------
    # Raw SQL filter helpers (for the semantic search text() query)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_raw_filters(request: SearchRequest | None) -> str:
        """Build raw SQL WHERE clause fragments for semantic search."""
        if request is None:
            return ""

        clauses: list[str] = []
        if request.sources:
            clauses.append("AND source_name = ANY(:sources)")
        if request.source_types:
            clauses.append("AND source_type = ANY(:source_types)")
        if request.language:
            clauses.append("AND language = :language")
        if request.from_date:
            clauses.append("AND published_at >= :from_date")
        if request.to_date:
            clauses.append("AND published_at <= :to_date")
        if not request.include_duplicates:
            clauses.append("AND is_duplicate = false")

        # Facet-style filters
        if request.sources_include:
            clauses.append("AND source_name = ANY(:sources_include)")
        if request.sources_exclude:
            clauses.append("AND source_name != ALL(:sources_exclude)")
        if request.languages_include:
            clauses.append("AND language = ANY(:languages_include)")
        if request.languages_exclude:
            clauses.append("AND language != ALL(:languages_exclude)")
        if request.forwarded is not None:
            clauses.append("AND (metadata_->>'forwarded')::boolean = :forwarded")
        if request.exclude_keywords:
            for i, _ in enumerate(request.exclude_keywords):
                clauses.append(f"AND content NOT ILIKE :exclude_kw_{i}")

        return "\n".join(clauses)

    @staticmethod
    def _build_raw_filter_params(request: SearchRequest | None) -> dict:
        """Build parameter dict for raw SQL filters."""
        if request is None:
            return {}

        params: dict = {}
        if request.sources:
            params["sources"] = request.sources
        if request.source_types:
            params["source_types"] = request.source_types
        if request.language:
            params["language"] = request.language
        if request.from_date:
            params["from_date"] = request.from_date
        if request.to_date:
            params["to_date"] = request.to_date

        # Facet-style filters
        if request.sources_include:
            params["sources_include"] = request.sources_include
        if request.sources_exclude:
            params["sources_exclude"] = request.sources_exclude
        if request.languages_include:
            params["languages_include"] = request.languages_include
        if request.languages_exclude:
            params["languages_exclude"] = request.languages_exclude
        if request.forwarded is not None:
            params["forwarded"] = request.forwarded
        if request.exclude_keywords:
            for i, kw in enumerate(request.exclude_keywords):
                params[f"exclude_kw_{i}"] = f"%{kw}%"

        return params

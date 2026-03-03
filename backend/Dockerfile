FROM --platform=linux/amd64 python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install runtime dependencies only (not the project itself) — preserves layer cache
# when only src/ changes.
RUN uv sync --frozen --no-cache --no-dev --no-install-project

# Copy application source and migration files
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini README.md ./

# Install the project itself now that src/ is present
RUN uv sync --frozen --no-cache --no-dev

# Pre-download the sentence-transformers model so it's baked into the image.
# The model is cached at /root/.cache/huggingface by default.
# Override EMBEDDING_MODEL build-arg to change the model.
ARG EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RUN /app/.venv/bin/python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
